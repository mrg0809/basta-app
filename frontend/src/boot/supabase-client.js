import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://ywspcbuozqcgtlsgukln.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3c3BjYnVvenFjZ3Rsc2d1a2xuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY1OTE2MDUsImV4cCI6MjA2MjE2NzYwNX0.q6G3s15eqr59uMLCLQMm-JCafXoBFxB_BMeqEqD66ck'

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Error: Supabase URL and Anon Key are required. Update src/boot/supabase-client.js');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    detectSessionInUrl: true,
    persistSession: true, // Esto es el valor por defecto, pero asegúrate de no tenerlo en false
    autoRefreshToken: true, // También por defecto
    // detectSessionInUrl: true, // Esto también es por defecto y crucial para OAuth
  }
  })      

export default ({ app }) => {
  app.config.globalProperties.$supabase = supabase
}