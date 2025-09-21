
(function(){
  function addButtons(){
    document.querySelectorAll('pre > code').forEach(function(code){
      const pre = code.parentElement;
      if(pre.classList.contains('has-copy')) return;
      pre.classList.add('has-copy');
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.type = 'button';
      btn.innerText = 'Kopiuj';
      btn.addEventListener('click', async function(){
        try {
          await navigator.clipboard.writeText(code.innerText);
          btn.innerText = 'Skopiowano!';
          setTimeout(()=>btn.innerText='Kopiuj', 1400);
        } catch(e){
          btn.innerText = 'Błąd';
          setTimeout(()=>btn.innerText='Kopiuj', 1400);
        }
      });
      pre.style.position = 'relative';
      btn.style.position = 'absolute';
      btn.style.top = '8px';
      btn.style.right = '8px';
      btn.style.padding = '4px 8px';
      btn.style.border = '1px solid var(--border)';
      btn.style.borderRadius = '8px';
      btn.style.background = 'rgba(255,255,255,0.05)';
      btn.style.color = 'inherit';
      btn.style.cursor = 'pointer';
      pre.appendChild(btn);
    });
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', addButtons);
  } else {
    addButtons();
  }
})();
