(function(){
  const data = window.SPICE_DATA || {};
  const analysis = data.analysis;
  const spice = data.spice;
  const modeSelect = document.getElementById('mode');
  const analysisSelect = document.getElementById('analysis');
  function updateAnalysisFields(){
    const a = analysisSelect ? analysisSelect.value : 'dc';
    document.querySelectorAll('.ac-only').forEach(el => el.style.display = (a==='ac') ? '' : 'none');
    document.querySelectorAll('.tran-only').forEach(el => el.style.display = (a==='tran') ? '' : 'none');
  }
  if (analysisSelect){ analysisSelect.addEventListener('change', updateAnalysisFields); updateAnalysisFields(); }

  function drawAxes(ctx,w,h,pad,opts){
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle='#fff'; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle='#8aa'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,pad.t); ctx.lineTo(pad.l,h-pad.b); ctx.lineTo(w-pad.r,h-pad.b); ctx.stroke();
    ctx.fillStyle='#234'; ctx.font='12px Tahoma, Arial, sans-serif';
    if(opts.xLabel){ ctx.fillText(opts.xLabel, w/2-30, h-6); }
    if(opts.yLabel){ ctx.save(); ctx.translate(14, h/2+20); ctx.rotate(-Math.PI/2); ctx.fillText(opts.yLabel,0,0); ctx.restore(); }
    if(opts.title){ ctx.font='bold 13px Tahoma, Arial, sans-serif'; ctx.fillText(opts.title, pad.l, 16); }
  }
  function ticks(min,max,n,log){
    if(log){
      const t=[]; let p=Math.pow(10, Math.floor(Math.log10(Math.max(min,1e-12))));
      for(;p<=max*1.01;p*=10){ t.push(p); }
      return t;
    }
    const step=(max-min)/n || 1; const t=[]; for(let i=0;i<=n;i++) t.push(min+step*i); return t;
  }
  function mapX(x,min,max,pad,w,log){ if(log){ const lx=Math.log10(Math.max(x,1e-12)), lmin=Math.log10(Math.max(min,1e-12)), lmax=Math.log10(Math.max(max,1e-12)); return pad.l + (lx-lmin)/(lmax-lmin||1)*(w-pad.l-pad.r);} return pad.l + (x-min)/(max-min||1)*(w-pad.l-pad.r); }
  function mapY(y,min,max,pad,h){ return (h-pad.b) - (y-min)/(max-min||1)*(h-pad.t-pad.b); }

  function linePlot(canvasId, series, opts){
    const c=document.getElementById(canvasId); if(!c||!series||!series.length) return;
    const ctx=c.getContext('2d'); const w=c.width, h=c.height; const pad={l:62,r:20,t:28,b:38};
    const xs=series.flatMap(s=>s.data.map(p=>p.x)).filter(Number.isFinite);
    const ys=series.flatMap(s=>s.data.map(p=>p.y)).filter(Number.isFinite);
    let xmin=opts.xmin??Math.min(...xs), xmax=opts.xmax??Math.max(...xs);
    let ymin=opts.ymin??Math.min(...ys), ymax=opts.ymax??Math.max(...ys);
    if(ymin===ymax){ ymin-=1; ymax+=1; }
    if(opts.yPad){ const d=(ymax-ymin)*opts.yPad; ymin-=d; ymax+=d; }
    drawAxes(ctx,w,h,pad,opts);
    ctx.fillStyle='#556'; ctx.font='11px Tahoma, Arial, sans-serif';
    const xt=ticks(xmin,xmax,6,opts.logX);
    xt.forEach(x=>{ const X=mapX(x,xmin,xmax,pad,w,opts.logX); ctx.strokeStyle='#d9e3ea'; ctx.beginPath(); ctx.moveTo(X,pad.t); ctx.lineTo(X,h-pad.b); ctx.stroke(); ctx.fillStyle='#556'; ctx.fillText(opts.logX?x.toExponential(0):x.toPrecision(4), X-10, h-pad.b+16); });
    const yt=ticks(ymin,ymax,5,false);
    yt.forEach(y=>{ const Y=mapY(y,ymin,ymax,pad,h); ctx.strokeStyle='#d9e3ea'; ctx.beginPath(); ctx.moveTo(pad.l,Y); ctx.lineTo(w-pad.r,Y); ctx.stroke(); ctx.fillStyle='#556'; ctx.fillText(y.toPrecision(4), 4, Y+4); });
    series.forEach(s=>{
      ctx.strokeStyle=s.color; ctx.lineWidth=s.width||2; ctx.beginPath();
      s.data.forEach((p,i)=>{ const X=mapX(p.x,xmin,xmax,pad,w,opts.logX), Y=mapY(p.y,ymin,ymax,pad,h); if(i===0) ctx.moveTo(X,Y); else ctx.lineTo(X,Y); });
      ctx.stroke();
    });
    let lx=w-pad.r-160, ly=pad.t+8;
    series.forEach(s=>{ ctx.fillStyle=s.color; ctx.fillRect(lx,ly-8,14,3); ctx.fillStyle='#234'; ctx.fillText(s.name,lx+20,ly-3); ly+=16; });
  }

  if(spice && analysis==='ac' && spice.ac){
    const rows=spice.ac;
    linePlot('ac-mag',[{name:'|Vout/Vin| (dB)', color:'#0b6b8a', data:rows.map(r=>({x:r.frequency_hz,y:r.gain_db}))}], {title:'Bode Magnitude', xLabel:'Frequency [Hz] (log)', yLabel:'Gain [dB]', logX:true, yPad:0.08});
    linePlot('ac-phase',[{name:'Phase(Vout/Vin) [deg]', color:'#b65a2a', data:rows.map(r=>({x:r.frequency_hz,y:r.phase_deg}))}], {title:'Bode Phase', xLabel:'Frequency [Hz] (log)', yLabel:'Phase [deg]', logX:true, ymin:-200,ymax:200});
  }
  if(spice && analysis==='tran' && spice.tran){
    const rows=spice.tran;
    linePlot('tran-plot',[
      {name:'Vin [V]', color:'#0b7f79', data:rows.map(r=>({x:r.time_s*1000,y:r.vin_v}))},
      {name:'Vout [V]', color:'#c96a2b', data:rows.map(r=>({x:r.time_s*1000,y:r.vout_v}))}
    ], {title:'Transient Response', xLabel:'Time [ms]', yLabel:'Voltage [V]', logX:false, yPad:0.1});
  }
})();
