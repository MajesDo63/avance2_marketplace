'use strict';
const $ = s => document.querySelector(s);
const money = value => new Intl.NumberFormat('es-MX', {style:'currency',currency:'USD',currencyDisplay:'narrowSymbol'}).format(Number(value));
function stored(storage, key, fallback) { try { return JSON.parse(storage.getItem(key)) || fallback; } catch { return fallback; } }
let session = stored(sessionStorage, 'cesar_session', null);
let cart = stored(localStorage, 'cesar_cart', []);
if (!Array.isArray(cart)) cart = [];
cart = cart.filter(x => Number.isInteger(x.producto_id) && Number.isInteger(x.cantidad) && x.cantidad > 0 && x.cantidad <= 99).slice(0,20);
let products = [], registerMode = false, toastTimer, category = 'todos';
const normalized = value => value.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
// Presentación: los IDs, precios y existencias provienen siempre de la API.
const categoryNames = {laptops:'Laptops',pc:'Computadoras',componentes:'Componentes',almacenamiento:'Almacenamiento',monitores:'Monitores',perifericos:'Periféricos',conectividad:'Conectividad',electronica:'Electrónica'};
function productType(name) {
  const n = normalized(name);
  const rules = [
    [/laptop|notebook|computadora portatil/,'laptops','laptop'],
    [/\bpc\b|computadora|compu |mini pc/,'pc','desktop'],
    [/\bram\b|memoria ddr/,'componentes','ram'],
    [/ssd|disco|memoria usb|microsd/,'almacenamiento','ssd'],
    [/tarjeta grafica|gpu/,'componentes','gpu'],
    [/procesador|cpu/,'componentes','processor'],
    [/tarjeta madre|motherboard/,'componentes','motherboard'],
    [/fuente de poder/,'componentes','powersupply'],
    [/gabinete/,'componentes','desktop'],
    [/enfriamiento|ventilador|disipador/,'componentes','cooling'],
    [/monitor|pantalla/,'monitores','monitor'],
    [/teclado/,'perifericos','keyboard'],
    [/mouse|raton/,'perifericos','mouse'],
    [/audifonos|headset|bocina/,'perifericos','headphones'],
    [/webcam|camara/,'perifericos','webcam'],
    [/microcontrolador|sensor|protoboard|electronica|soldadura|resistor/,'electronica','electronics'],
    [/router|switch|ethernet|wifi/,'conectividad','router'],
    [/hub|adaptador|cable|cargador/,'conectividad','hub']
  ];
  const match=rules.find(([pattern])=>pattern.test(n));
  return match ? {category:match[1],icon:match[2]} : {category:'perifericos',icon:'hub'};
}
function selectCategory(value, scroll=false) {
  category=value;
  document.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.category===value)));
  renderProducts();
  if(scroll) { location.hash='#tienda'; $('#tienda').scrollIntoView({block:'start'}); }
}
const element = (tag, text, className) => { const e=document.createElement(tag); if(text!==undefined) e.textContent=text; if(className) e.className=className; return e; };
function toast(message) { $('#toast').textContent=message; $('#toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#toast').hidden=true,5000); }
function saveCart() { localStorage.setItem('cesar_cart',JSON.stringify(cart)); $('#cart-count').textContent=cart.reduce((n,x)=>n+x.cantidad,0); }
function showSession() { $('#login-button').hidden=!!session; $('#logout-button').hidden=!session; $('#logout-button').textContent=session ? session.usuario+' · Salir' : 'Salir'; }
function clearSession() { session=null; sessionStorage.removeItem('cesar_session'); showSession(); }
function authMode(register) {
  registerMode=register; $('#auth-form').reset(); $('#auth-message').textContent='';
  $('#auth-title').textContent=register?'Tu cuenta empieza aquí.':'Qué gusto verte.';
  $('#auth-subtitle').textContent=register?'Usa una contraseña de al menos 12 caracteres.':'Inicia sesión para comprar, publicar y ver tus pedidos.';
  $('#auth-submit').textContent=register?'Crear cuenta':'Iniciar sesión';
  $('#auth-toggle').textContent=register?'Ya tengo cuenta · Iniciar sesión':'¿Primera vez aquí? Crear una cuenta';
  $('#auth-form [name=password]').autocomplete=register?'new-password':'current-password';
}
function openAuth() { authMode(false); if(!$('#auth-dialog').open) $('#auth-dialog').showModal(); }
function requireSession() { if(session) return true; openAuth(); return false; }
async function api(path, options={}) {
  const headers={...(options.body ? {'Content-Type':'application/json'}:{}),...(session ? {Authorization:'Bearer '+session.token_sesion}:{}),...options.headers};
  const response=await fetch(path,{...options,headers});
  if(options.blob && response.ok) return response.blob();
  const data=await response.json().catch(()=>({error:'El servidor no devolvió una respuesta válida.'}));
  if(!response.ok) { if(response.status===401 && path!='/login') clearSession(); throw new Error(data.error || 'No se pudo completar la operación.'); }
  return data;
}
async function loadProducts() {
  try { products=(await api('/productos')).catalogo; $('#catalog-error').hidden=true; renderProducts(); }
  catch(e) { $('#catalog-count').textContent='Catálogo no disponible'; $('#catalog-error').textContent=e.message; $('#catalog-error').hidden=false; }
}
function renderProducts() {
  const search=normalized($('#search').value.trim());
  let items=products.filter(p=>(category==='todos'||productType(p.nombre).category===category) && normalized(p.nombre+' '+categoryNames[productType(p.nombre).category]).includes(search));
  if($('#sort').value==='default') {
    const order=Object.keys(categoryNames);
    items.sort((a,b)=>order.indexOf(productType(a.nombre).category)-order.indexOf(productType(b.nombre).category)||a.id-b.id);
  }
  if($('#sort').value==='low') items.sort((a,b)=>Number(a.precio)-Number(b.precio));
  if($('#sort').value==='high') items.sort((a,b)=>Number(b.precio)-Number(a.precio));
  $('#catalog-count').textContent=`${items.length} producto${items.length===1?'':'s'} · Precios de práctica en USD`;
  const grid=$('#productos-grid'); grid.replaceChildren();
  for(const p of items) {
    const card=$('#product-template').content.cloneNode(true);
    card.querySelector('h3').textContent=p.nombre;
    card.querySelector('.stock').textContent=p.stock>0 ? `${p.stock} ${p.stock===1?'unidad disponible':'unidades disponibles'}` : 'Sin existencias por el momento';
    card.querySelector('.price').append(document.createTextNode(money(p.precio)),element('small','USD'));
    const type=productType(p.nombre);
    card.querySelector('img').src='/static/'+type.icon+'.svg';
    card.querySelector('.product-category').textContent=categoryNames[type.category];
    card.querySelector('.product-tag').textContent=p.stock>0?'EN STOCK':'AGOTADO';
    const button=card.querySelector('.add-button'); button.disabled=p.stock<=0; button.setAttribute('aria-label','Agregar '+p.nombre+' al carrito');
    button.addEventListener('click',()=>addProduct(p)); grid.append(card);
  }
  if(!items.length) grid.append(element('p','No encontramos productos con esos filtros. Prueba otra búsqueda o selecciona Todo el catálogo.','empty'));
}
function addProduct(p) {
  const item=cart.find(x=>x.producto_id===p.id);
  if(item && item.cantidad>=Math.min(p.stock,99)) return toast('Ya agregaste las unidades disponibles.');
  if(item) item.cantidad++; else { if(cart.length>=20) return toast('Máximo 20 productos diferentes por pedido.'); cart.push({producto_id:p.id,cantidad:1}); }
  saveCart(); toast(p.nombre+' agregado al carrito.');
}
function renderCart() {
  const panel=$('#cart-items'); panel.replaceChildren(); let total=0;
  if(!cart.length) panel.append(element('p','Tu carrito está vacío. Explora el catálogo para agregar productos.','empty'));
  for(const item of cart) {
    const p=products.find(p=>p.id===item.producto_id);
    const row=element('div',undefined,'cart-row'), info=element('div'), actions=element('div');
    info.append(element('strong',p ? p.nombre : 'Producto no disponible'),element('p',p ? money(p.precio)+' USD por unidad' : 'Elimina este producto para continuar.'));
    const quantity=element('input'); quantity.type='number'; quantity.min='1'; quantity.max=String(Math.min(p?.stock || 99,99)); quantity.value=item.cantidad; quantity.className='quantity'; quantity.setAttribute('aria-label','Cantidad de '+(p?.nombre || 'producto'));
    quantity.addEventListener('input',()=>{ const n=Number(quantity.value); if(!Number.isInteger(n)||n<1||n>99) return; item.cantidad=n; saveCart(); $('#cart-total').textContent=money(cart.reduce((sum,x)=>sum+Number(products.find(product=>product.id===x.producto_id)?.precio||0)*x.cantidad,0))+' USD'; });
    quantity.addEventListener('change',()=>{ const n=Number(quantity.value); if(!Number.isInteger(n)||n<1||n>99) return renderCart(); item.cantidad=n; saveCart(); renderCart(); });
    const remove=element('button','Quitar','remove'); remove.type='button'; remove.addEventListener('click',()=>{cart=cart.filter(x=>x!==item);saveCart();renderCart();});
    actions.append(quantity,element('br'),remove); row.append(info,actions); panel.append(row); if(p) total+=Number(p.precio)*item.cantidad;
  }
  $('#cart-total').textContent=money(total)+' USD'; $('#checkout-form button').disabled=!cart.length;
}
async function renderOrders() {
  const list=$('#orders-list'); list.replaceChildren();
  if(!session) { list.append(element('p','Inicia sesión para consultar tus pedidos.','empty')); return; }
  list.append(element('p','Cargando tus pedidos…','empty'));
  try {
    const orders=(await api('/pedidos')).pedidos; list.replaceChildren();
    if(!orders.length) list.append(element('p','Aún no tienes pedidos. Tus próximas compras aparecerán aquí.','empty'));
    for(const order of orders) {
      const card=element('article',undefined,'panel order'), top=element('div',undefined,'order-top'), text=element('div');
      text.append(element('h3','Pedido #'+order.id),element('span',order.s3_comprobante_key?'Comprobante disponible':'Comprobante pendiente','badge'));
      top.append(text,element('strong',money(order.total)+' USD')); card.append(top);
      let detail=order.detalle; try{const lines=JSON.parse(detail); if(Array.isArray(lines)) detail=lines.map(x=>x.nombre+' × '+x.cantidad).join(' · ');}catch{}
      card.append(element('p',detail),element('p','Comprobante para '+order.correo_comprador));
      const actions=element('div',undefined,'order-actions'), download=element('button','Descargar comprobante','button secondary'), resend=element('button','Reenviar confirmación','button secondary');
      download.disabled=!order.s3_comprobante_key;
      download.addEventListener('click',async()=>{ download.disabled=true;try{const blob=await api(`/pedidos/${order.id}/comprobante`,{blob:true});const url=URL.createObjectURL(blob),a=element('a');a.href=url;a.download=`pedido-${order.id}.txt`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}catch(e){toast(e.message);}finally{download.disabled=false;} });
      resend.addEventListener('click',async()=>{resend.disabled=true;try{await api(`/pedidos/${order.id}/reenviar-confirmacion`,{method:'POST'});toast('El servicio de correo aceptó la confirmación. Revisa tu bandeja de entrada y spam.');await renderOrders();}catch(e){toast(e.message);resend.disabled=false;}});
      actions.append(download,resend);card.append(actions);list.append(card);
    }
  } catch(e) { list.replaceChildren(element('p',e.message,'inline-error')); }
}
function navigate() {
  let view=location.hash.slice(1); if(!['carrito','pedidos','publicar'].includes(view)) view='catalogo';
  for(const name of ['catalogo','carrito','pedidos','publicar']) $('#'+name+'-view').hidden=name!==view;
  document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+view));
  document.title='César Tech · '+({catalogo:'Tienda',carrito:'Carrito',pedidos:'Mis pedidos',publicar:'Publicar'}[view]);
  if(view==='carrito') renderCart(); if(view==='pedidos') renderOrders();
  if(view==='publicar'&&!session) openAuth();
}
$('#auth-toggle').addEventListener('click',()=>authMode(!registerMode));
$('#auth-form').addEventListener('submit',async e=>{e.preventDefault();const button=$('#auth-submit');button.disabled=true;$('#auth-message').textContent='';const form=new FormData(e.target),body=JSON.stringify({usuario:form.get('usuario'),password:form.get('password')});try{if(registerMode)await api('/registro',{method:'POST',body});session=await api('/login',{method:'POST',body});sessionStorage.setItem('cesar_session',JSON.stringify(session));showSession();e.target.reset();$('#auth-dialog').close();toast('Bienvenido, '+session.usuario+'.');navigate();}catch(err){$('#auth-message').textContent=err.message;}finally{button.disabled=false;}});
$('#checkout-form').addEventListener('submit',async e=>{e.preventDefault();if(!requireSession())return;const button=e.target.querySelector('button');button.disabled=true;$('#checkout-message').textContent='Verificando disponibilidad…';try{await api('/carrito',{method:'POST',body:JSON.stringify({items:cart})});const order=await api('/ordenes/checkout',{method:'POST',body:JSON.stringify({items:cart,correo:new FormData(e.target).get('correo')})});cart=[];saveCart();$('#checkout-message').textContent='';toast(order.confirmacion==='confirmada'?'Pedido #'+order.pedido_id+' confirmado.':'Pedido registrado; la confirmación está pendiente. No repitas la compra.');await loadProducts();location.hash='#pedidos';}catch(err){$('#checkout-message').textContent=err.message;}finally{button.disabled=false;}});
$('#publish-form').addEventListener('submit',async e=>{e.preventDefault();if(!requireSession())return;const button=e.target.querySelector('button');button.disabled=true;$('#publish-message').textContent='';const f=new FormData(e.target);try{await api('/productos',{method:'POST',body:JSON.stringify({nombre:f.get('nombre'),precio:f.get('precio'),stock:Number(f.get('stock'))})});e.target.reset();await loadProducts();location.hash='#catalogo';toast('Tu producto ya está en el catálogo.');}catch(err){$('#publish-message').textContent=err.message;}finally{button.disabled=false;}});
$('#login-button').addEventListener('click',openAuth);$('#logout-button').addEventListener('click',()=>{clearSession();cart=[];saveCart();location.hash='#catalogo';toast('Cerraste tu sesión en este navegador.');});$('.close-dialog').addEventListener('click',()=>$('#auth-dialog').close());
$('#search').addEventListener('input',renderProducts);$('#sort').addEventListener('change',renderProducts);window.addEventListener('hashchange',navigate);
document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>selectCategory(button.dataset.category)));
document.querySelectorAll('[data-category-link]').forEach(button=>button.addEventListener('click',()=>{ $('#search').value=''; selectCategory(button.dataset.categoryLink,true); }));
saveCart();showSession();loadProducts().then(navigate);
