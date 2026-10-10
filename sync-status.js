/* Indicador MarketScope: execução da pesquisa e gravação do catálogo são factos distintos. */
(function () {
 const repo='bruno1996santos-jpg/marketscope-pneus-portugal';
 const catalog='monitorizacao/relatorio_diario.json';
 const statusFile='monitorizacao/estado_pesquisa.json';
 const cutoffHours=30;
 const datePt=iso=>new Intl.DateTimeFormat('pt-PT',{dateStyle:'short',timeStyle:'short',timeZone:'Europe/Lisbon'}).format(new Date(iso));
 function line(text,warning){const p=document.createElement('div');p.textContent=text;p.style.marginBottom='5px';if(warning)p.style.fontWeight='600';return p}
 function link(to,label){const a=document.createElement('a');a.href=to;a.rel='noopener noreferrer';a.target='_blank';a.textContent=label;return a}
 async function refresh(){
  let box=document.getElementById('marketscope-sync-status');
  if(!box){box=document.createElement('section');box.id='marketscope-sync-status';const anchor=document.querySelector('main .heading, main header, .top, header')||document.body;anchor.insertAdjacentElement('afterend',box)}
  box.setAttribute('role','status');
  box.style.cssText='margin:12px 0;padding:12px 15px;border:1px solid #c8d9e4;background:#edf5fa;border-radius:9px;font:13px system-ui;line-height:1.6;color:#283648';
  box.replaceChildren(line('A verificar o estado da monitorização…'));
  const problems=[];
  try{
   const response=await fetch(statusFile+'?t='+Date.now(),{cache:'no-store'});
   if(!response.ok)throw new Error('HTTP '+response.status);
   const status=await response.json();
   box.replaceChildren();
   const completed=status.last_completed_at;
   if(completed&&Number.isFinite(Date.parse(completed))){
    const age=(Date.now()-Date.parse(completed))/3600000;
    box.appendChild(line('Pesquisa diária: última execução reportada em '+datePt(completed)+'.',false));
    if(age>cutoffHours)problems.push('Última pesquisa reportada há mais de 30 horas.');
   }else{
    box.appendChild(line('Pesquisa diária: ainda sem execução automaticamente comprovada.',true));
    problems.push('A ligação da tarefa diária ao registo de execução ainda não está validada.');
   }
   const written=status.last_write_at;
   if(status.write_status==='success'&&written&&Number.isFinite(Date.parse(written))){
    box.appendChild(line('Atualização pelo relatório diário: escrita comunicada em '+datePt(written)+'.',false));
   }else{
    box.appendChild(line('Atualização pelo relatório diário: nenhuma escrita automática confirmada.',true));
    if(completed)problems.push('A pesquisa foi reportada, mas a escrita dos resultados não está confirmada.');
   }
   if(status.last_result==='failed')problems.push('A pesquisa diária reportou uma falha.');
   if(status.write_status==='failed')problems.push('A tarefa diária reportou erro de gravação no GitHub.');
  }catch(e){
   box.replaceChildren(line('Pesquisa diária: estado indisponível. ('+e.message+')',true));
   problems.push('Não é possível confirmar a última pesquisa.');
  }
  try {
   const response=await fetch('monitorizacao/estado_verificacao_fontes.json?t='+Date.now(),{cache:'no-store'});
   if(response.ok){
    const technical=await response.json();
    if(technical.last_completed_at&&Number.isFinite(Date.parse(technical.last_completed_at))){
     box.appendChild(line('Verificação técnica de fontes (GitHub Actions): '+datePt(technical.last_completed_at)+'; '+technical.sources_accessible+'/'+technical.sources_checked+' URLs acessíveis. Não substitui a pesquisa de campanhas.'));
    }
   }
  } catch(e) { /* A verificação técnica é informação complementar. */ }
  try{
   const r=await fetch('https://api.github.com/repos/'+repo+'/commits?path='+encodeURIComponent(catalog)+'&per_page=1&t='+Date.now(),{cache:'no-store',headers:{Accept:'application/vnd.github+json'}});
   if(!r.ok)throw new Error('HTTP '+r.status);
   const commits=await r.json();
   const timestamp=commits?.[0]?.commit?.committer?.date||commits?.[0]?.commit?.author?.date;
   if(!timestamp||!Number.isFinite(Date.parse(timestamp)))throw new Error('sem data');
   box.appendChild(line('Base de campanhas: última gravação efetiva no GitHub em '+datePt(timestamp)+'.'));
   const p=document.createElement('div');
   p.appendChild(link('https://github.com/'+repo+'/commits/main/'+catalog,'Ver histórico de alterações ↗'));
   box.appendChild(p);
   // Não assinalar falta de novidades como erro: uma pesquisa pode não encontrar alterações.
  }catch(e){problems.push('Não foi possível confirmar a gravação da base de campanhas.');}
  if(problems.length){
   box.style.borderColor='#eabf71';box.style.background='#fff7e8';
   box.appendChild(line('⚠ '+problems.join(' '),true));
  }
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh,{once:true});else refresh();
 window.refreshMarketScopeSyncStatus=refresh;
})();
