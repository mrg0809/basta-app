from postgrest.exceptions import APIError
import random
import string
from collections import Counter
from uuid import UUID
from supabase import Client
import logging

logger = logging.getLogger(__name__)

def generate_room_code(length: int = 6) -> str:
    """Generates a random alphanumeric room code."""
    # Usaremos letras mayúsculas y dígitos para evitar ambigüedades (ej. O vs 0, I vs 1)
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


async def calculate_round_scores(room_id: UUID, round_number: int, supabase_client: Client, current_letter: str):
    room_id_str = str(room_id)
    logger.info(f"Calculating scores for room {room_id_str}, round {round_number}, letter '{current_letter}'.")

    try:
        answers_resp = supabase_client.table("player_round_answers") \
            .select("id, room_participant_id, category_id, answer_text") \
            .eq("game_room_id", room_id_str) \
            .eq("round_number", round_number) \
            .execute()

        if not answers_resp.data:
            logger.warning(f"No answers for room {room_id_str}, R{round_number}. Marking round_over_results.")
            supabase_client.table("game_rooms").update({"status": "round_over_results"}).eq("id", room_id_str).execute()
            return

        all_answers_for_round = answers_resp.data
        processed_answers = []
        answers_grouped_by_category = {}

        for ans_row in all_answers_for_round:
            text_original = ans_row["answer_text"] or ""
            detail = {
                "answer_db_id": ans_row["id"],
                "participant_id": str(ans_row["room_participant_id"]),
                "category_id": str(ans_row["category_id"]),
                "text_original": text_original,
                "text_normalized": text_original.strip().lower(),
                "score": 0, "is_valid": False, "notes": ""
            }
            processed_answers.append(detail)

            if not detail["text_normalized"]:
                detail["notes"] = "Vacía"
            elif not detail["text_normalized"].startswith(current_letter.lower()):
                detail["notes"] = "Letra incorrecta"
            else:
                detail["is_valid"] = True
                cat_answers = answers_grouped_by_category.setdefault(detail["category_id"], {})
                cat_answers.setdefault(detail["text_normalized"], []).append(detail["participant_id"])
        
        player_total_round_scores = Counter()

        for ans_detail in processed_answers:
            if ans_detail["is_valid"]:
                cat_id = ans_detail["category_id"]
                norm_text = ans_detail["text_normalized"]
                repetition_count = len(answers_grouped_by_category.get(cat_id, {}).get(norm_text, []))
                
                if repetition_count == 1:
                    ans_detail["score"] = 100
                    ans_detail["notes"] = "Única (100 pts)"
                elif repetition_count > 1:
                    points_per_player = int(100 / repetition_count)
                    ans_detail["score"] = points_per_player
                    ans_detail["notes"] = f"Repetida ({repetition_count} veces, {points_per_player} pts c/u)"
                else:
                    ans_detail["notes"] = "Error en conteo" 
            player_total_round_scores[ans_detail["participant_id"]] += ans_detail["score"]
        
        if processed_answers:
            logger.info(f"Updating scores for {len(processed_answers)} individual answers in player_round_answers.")
            for ans_detail in processed_answers:
                supabase_client.table("player_round_answers") \
                    .update({
                        "score_awarded": ans_detail["score"],
                        "is_valid": ans_detail["is_valid"],
                        "validation_notes": ans_detail["notes"]
                    }) \
                    .eq("id", ans_detail["answer_db_id"]) \
                    .execute()

        if player_total_round_scores:
            logger.info(f"Updating total scores for {len(player_total_round_scores)} participants.")
            for p_id_str, round_score_for_player in player_total_round_scores.items():
                # Leer el score actual del participante específico para sumarle el de la ronda
                current_participant_score_resp = supabase_client.table("room_participants") \
                    .select("score") \
                    .eq("id", p_id_str) \
                    .single() \
                    .execute()
                
                current_db_score = 0
                if current_participant_score_resp.data:
                    current_db_score = current_participant_score_resp.data.get("score", 0)
                else:
                    logger.warning(f"Could not fetch current score for participant {p_id_str} to update. Assuming 0.")

                new_total_score = current_db_score + round_score_for_player
                
                # --- Realizar UPDATE individual para room_participants ---
                supabase_client.table("room_participants") \
                    .update({"score": new_total_score}) \
                    .eq("id", p_id_str) \
                    .execute()
                # -------------------------------------------------------
        
        logger.info(f"Finished scoring for room {room_id_str}, R{round_number}. Setting status to 'round_over_results'.")
        supabase_client.table("game_rooms").update({"status": "round_over_results"}).eq("id", room_id_str).execute()
        logger.info(f"Scores calculated, room status updated for room {room_id_str}.")

    except APIError as e:
        logger.error(f"Supabase APIError in calculate_round_scores for room {room_id_str}: {e.message}", exc_info=False)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in calculate_round_scores for room {room_id_str}: {str(e)}", exc_info=True)
        raise