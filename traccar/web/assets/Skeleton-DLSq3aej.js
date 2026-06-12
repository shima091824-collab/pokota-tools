import{i as e}from"./chunk-aKtaBQYM.js";import{Ft as t,H as n,R as r,Y as i,at as a,bt as o,it as s,ot as c,vt as l,xt as u,z as d}from"./mui-BgU4WrXF.js";function f(e){return String(e).match(/[\d.\-+]*\s*(.*)/)[1]||``}function p(e){return parseFloat(e)}var m=e(t(),1);function h(e){return a(`MuiSkeleton`,e)}s(`MuiSkeleton`,[`root`,`text`,`rectangular`,`rounded`,`circular`,`pulse`,`wave`,`withChildren`,`fitContent`,`heightAuto`]);var g=l(),_=e=>{let{classes:t,variant:n,animation:r,hasChildren:a,width:o,height:s}=e;return i({root:[`root`,n,r,a&&`withChildren`,a&&!o&&`fitContent`,a&&!s&&`heightAuto`]},h,t)},v=u`
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }

  100% {
    opacity: 1;
  }
`,y=u`
  0% {
    transform: translateX(-100%);
  }

  50% {
    /* +0.5s of delay between each loop */
    transform: translateX(100%);
  }

  100% {
    transform: translateX(100%);
  }
`,b=typeof v==`string`?null:o`
        animation: ${v} 2s ease-in-out 0.5s infinite;
      `,x=typeof y==`string`?null:o`
        &::after {
          animation: ${y} 2s linear 0.5s infinite;
        }
      `,S=n(`span`,{name:`MuiSkeleton`,slot:`Root`,overridesResolver:(e,t)=>{let{ownerState:n}=e;return[t.root,t[n.variant],n.animation!==!1&&t[n.animation],n.hasChildren&&t.withChildren,n.hasChildren&&!n.width&&t.fitContent,n.hasChildren&&!n.height&&t.heightAuto]}})(d(({theme:e})=>{let t=f(e.shape.borderRadius)||`px`,n=p(e.shape.borderRadius);return{display:`block`,backgroundColor:e.vars?e.vars.palette.Skeleton.bg:e.alpha(e.palette.text.primary,e.palette.mode===`light`?.11:.13),height:`1.2em`,variants:[{props:{variant:`text`},style:{marginTop:0,marginBottom:0,height:`auto`,transformOrigin:`0 55%`,transform:`scale(1, 0.60)`,borderRadius:`${n}${t}/${Math.round(n/.6*10)/10}${t}`,"&:empty:before":{content:`"\\00a0"`}}},{props:{variant:`circular`},style:{borderRadius:`50%`}},{props:{variant:`rounded`},style:{borderRadius:(e.vars||e).shape.borderRadius}},{props:({ownerState:e})=>e.hasChildren,style:{"& > *":{visibility:`hidden`}}},{props:({ownerState:e})=>e.hasChildren&&!e.width,style:{maxWidth:`fit-content`}},{props:({ownerState:e})=>e.hasChildren&&!e.height,style:{height:`auto`}},{props:{animation:`pulse`},style:b||{animation:`${v} 2s ease-in-out 0.5s infinite`}},{props:{animation:`wave`},style:{position:`relative`,overflow:`hidden`,WebkitMaskImage:`-webkit-radial-gradient(white, black)`,"&::after":{background:`linear-gradient(
                90deg,
                transparent,
                ${(e.vars||e).palette.action.hover},
                transparent
              )`,content:`""`,position:`absolute`,transform:`translateX(-100%)`,bottom:0,left:0,right:0,top:0}}},{props:{animation:`wave`},style:x||{"&::after":{animation:`${y} 2s linear 0.5s infinite`}}}]}})),C=m.forwardRef(function(e,t){let n=r({props:e,name:`MuiSkeleton`}),{animation:i=`pulse`,className:a,component:o=`span`,height:s,style:l,variant:u=`text`,width:d,...f}=n,p={...n,animation:i,component:o,variant:u,hasChildren:!!f.children};return(0,g.jsx)(S,{as:o,ref:t,className:c(_(p).root,a),ownerState:p,...f,style:{width:d,height:s,...l}})});export{C as t};