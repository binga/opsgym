const leaderboard=[
  {agent:"Northstar Large",harness:"tool-loop v1",score:71.8,pass:70,cost:"$3.84"},
  {agent:"Axiom Reasoner",harness:"tool-loop v1",score:64.5,pass:60,cost:"$2.91"},
  {agent:"Meridian Pro",harness:"tool-loop v1",score:57.3,pass:50,cost:"$1.76"},
  {agent:"Relay Medium",harness:"tool-loop v1",score:43.9,pass:40,cost:"$0.88"},
  {agent:"Local 32B",harness:"json-tools",score:31.2,pass:30,cost:"$0.19"},
  {agent:"Random baseline",harness:"built-in",score:3.4,pass:0,cost:"—"}
];
const body=document.querySelector("#leaderboard-body");
leaderboard.forEach((row,i)=>body.insertAdjacentHTML("beforeend",`<tr><td class="rank">${String(i+1).padStart(2,"0")}</td><td class="agent">${row.agent}<span class="synthetic">SYNTHETIC</span></td><td>${row.harness}</td><td class="score">${row.score.toFixed(1)}<div class="bar"><span style="width:${row.score}%"></span></div></td><td>${row.pass}%</td><td>${row.cost}</td></tr>`));

let ideas=[];
const domainFilter=document.querySelector("#domain-filter");
const modeFilter=document.querySelector("#mode-filter");
const grid=document.querySelector("#task-grid");
const count=document.querySelector("#task-count");
function render(){
  const filtered=ideas.filter(x=>(domainFilter.value==="all"||x.domain===domainFilter.value)&&(modeFilter.value==="all"||x.mode===modeFilter.value));
  count.textContent=`Showing ${filtered.length} of ${ideas.length} environment concepts`;
  grid.innerHTML=filtered.map(x=>`<article class="task-card"><div class="domain">${x.domain}</div><h3>${x.title}</h3><p>${x.observable_goal}</p><div class="meta"><span class="chip mode">${x.mode}</span><span class="chip">${x.difficulty}</span>${x.tools.slice(0,2).map(t=>`<span class="chip">${t}</span>`).join("")}</div></article>`).join("");
}
fetch("data/catalog.json").then(r=>r.json()).then(data=>{ideas=data;[...new Set(ideas.map(x=>x.domain))].sort().forEach(x=>domainFilter.insertAdjacentHTML("beforeend",`<option>${x}</option>`));render()}).catch(()=>{grid.innerHTML="<p>Catalog data could not be loaded. Serve this directory over HTTP instead of opening the file directly.</p>"});
domainFilter.addEventListener("change",render);modeFilter.addEventListener("change",render);
