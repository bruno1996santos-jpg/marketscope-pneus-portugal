// MarketScope private review module
const MS_SUPABASE_URL = 'https://lgjrnuelvwsvmbusufvu.supabase.co';
const MS_SUPABASE_KEY = 'sb_publishable_VAeZZvYfq134xQVSJ0APxQ_f1x75mXG';
const msDb = window.supabase.createClient(MS_SUPABASE_URL, MS_SUPABASE_KEY);
const MS_OWNER = 'bruno1996santos@gmail.com';
async function msSignIn(email, password) {
  const { error } = await msDb.auth.signInWithPassword({ email: email.trim(), password });
  if (error) throw error;
  const { data: { user } } = await msDb.auth.getUser();
  if (user?.email?.toLowerCase() !== MS_OWNER) { await msDb.auth.signOut(); throw new Error('Esta conta não está autorizada a rever campanhas.'); }
  return user;
}
async function msRequireOwner() {
  const { data: { session } } = await msDb.auth.getSession();
  if (!session) return null;
  const { data: { user }, error } = await msDb.auth.getUser();
  if (error || user?.email?.toLowerCase() !== MS_OWNER) { await msDb.auth.signOut(); return null; }
  return user;
}
async function msGetCampaigns() {
  const { data, error } = await msDb.from('campaigns').select('*').order('created_at', { ascending: false });
  if (error) throw error;
  return data || [];
}
async function msSaveCampaign(row) {
  const { error } = await msDb.from('campaigns').upsert(row, { onConflict: 'candidate_id' });
  if (error) throw error;
}
async function msLogout() { const { error } = await msDb.auth.signOut(); if (error) throw error; }
