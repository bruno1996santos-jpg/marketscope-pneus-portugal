/* MarketScope — transparência da sincronização.
   A API de commits confirma apenas a última ESCRITA no JSON, não a execução da pesquisa diária. */
(function () {
  const REPO = 'bruno1996santos-jpg/marketscope-pneus-portugal';
  const FILE = 'monitorizacao/relatorio_diario.json';
  const MAX_AGE_HOURS = 30;
  const containerId = 'marketscope-sync-status';
  function datePt(value) {
    return new Intl.DateTimeFormat('pt-PT', {dateStyle:'short',timeStyle:'short',timeZone:'Europe/Lisbon'}).format(new Date(value));
  }
  function show(target, text, warning) {
    target.textContent = text;
    target.style.cssText = 'margin:12px 0;padding:12px 15px;border:1px solid '+(warning?'#eabf71':'#c8d9e4')+';background:'+(warning?'#fff7e8':'#edf5fa')+';border-radius:9px;font:13px system-ui;line-height:1.5;color:#283648';
    target.setAttribute('role','status');
  }
  async function refresh() {
    let target=document.getElementById(containerId);
    if(!target) {
      target=document.createElement('div');
      target.id=containerId;
      const host=document.querySelector('main .heading, main header, .top, header') || document.body;
      host.insertAdjacentElement('afterend',target);
    }
    show(target,'A verificar a última alteração dos dados do MarketScope…',false);
    try {
      const r=await fetch('https://api.github.com/repos/'+REPO+'/commits?path='+encodeURIComponent(FILE)+'&per_page=1&t='+Date.now(),{cache:'no-store',headers:{Accept:'application/vnd.github+json'}});
      if(!r.ok) throw new Error('HTTP '+r.status);
      const commits=await r.json();
      if(!Array.isArray(commits)||!commits.length)throw new Error('Sem histórico de alterações');
      const c=commits[0], timestamp=c.commit?.committer?.date || c.commit?.author?.date;
      if(!timestamp||isNaN(Date.parse(timestamp)))throw new Error('Data de alteração indisponível');
      const age=(Date.now()-Date.parse(timestamp))/3600000;
      const stale=age>MAX_AGE_HOURS;
      const msg=stale
        ? '⚠ Dados sem alterações há mais de 30 horas. Última gravação no GitHub: '+datePt(timestamp)+'. Confirma no relatório diário se a pesquisa conseguiu atualizar o MarketScope.'
        : 'Última gravação dos dados no GitHub: '+datePt(timestamp)+'. Esta data confirma a alteração do ficheiro, não garante que a pesquisa diária tenha terminado ou descoberto novas campanhas.';
      show(target,msg,stale);
      const link=document.createElement('a');
      link.href='https://github.com/'+REPO+'/commits/main/'+FILE;
      link.target='_blank';link.rel='noopener noreferrer';
      link.textContent=' Ver histórico de alterações ↗';
      link.style.marginLeft='6px';
      target.appendChild(link);
    } catch(e) {
      show(target,'⚠ Não foi possível confirmar quando os dados foram atualizados no GitHub. Confirma o relatório diário ou consulta o histórico de alterações. ('+e.message+')',true);
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh,{once:true});
  else refresh();
  window.refreshMarketScopeSyncStatus=refresh;
})();
