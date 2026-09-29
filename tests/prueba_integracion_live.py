"""Live QA checks with unique disposable fixtures; preserves existing data."""
import json
import os
import secrets
import uuid
import requests
from app.db import cursor_db
from app.notificaciones import cliente_s3

base='http://127.0.0.1:5000'
recipient=os.environ.get('QA_EMAIL_DESTINATION', '')
if not recipient or os.environ.get('QA_ALLOW_REAL_EMAIL') != '1':
    raise RuntimeError('Configura QA_EMAIL_DESTINATION con el buzón autorizado y QA_ALLOW_REAL_EMAIL=1. Esta prueba envía dos correos reales.')
prefix='qa_auto_'+uuid.uuid4().hex[:10]
checks=[]
users=[]
product=None
order_ids=[]


def request(method,path,status=200,token=None,**kwargs):
    response=requests.request(method,base+path,headers={'Authorization':'Bearer '+token} if token else {},timeout=20,**kwargs)
    assert response.status_code==status, f'{method} {path}: {response.status_code} != {status}'
    return response


def check(label):
    checks.append(label)
    print('PASS: '+label,flush=True)


try:
    health=request('GET','/salud').json()
    assert all(health[k]=='conectado' for k in ['base_datos_rds','almacenamiento_s3','notificaciones'])
    check('Salud real: RDS, S3 y microservicio')
    for index in range(2):
        username=prefix+'_'+str(index)
        password=secrets.token_urlsafe(24)
        body={'usuario':username,'password':password}
        user_id=request('POST','/registro',201,json=body).json()['usuario_id']
        users.append({'id':user_id,'usuario':username})
        token=request('POST','/login',json=body).json()['token_sesion']
        users[-1]['token']=token
        request('POST','/registro',409,json=body)
        request('POST','/login',401,json={'usuario':username,'password':secrets.token_urlsafe(24)})
    check('Registro, hash/login, duplicados y contraseña incorrecta')
    a,b=users
    request('POST','/ordenes/checkout',401,json={})
    request('POST','/pedidos/2147483647/reenviar-confirmacion',401,token='token-seguro-usr-1')
    check('Compra anónima y token falsificado rechazados')
    product=request('POST','/productos',201,token=a['token'],json={'nombre':prefix+'_producto','precio':'12.50','stock':3}).json()['producto_id']
    check('Publicación en RDS sin colisiones de identificadores')
    items=[{'producto_id':product,'cantidad':2,'precio':0.01}]
    quote=request('POST','/carrito',token=a['token'],json={'items':items}).json()
    assert quote['total']=='25.00'
    check('Carrito calcula el precio real del servidor')
    order=request('POST','/ordenes/checkout',201,token=a['token'],json={'usuario_id':b['id'],'total':0.01,'correo':recipient,'items':items}).json()
    order_ids.append(order['pedido_id'])
    assert order['total']=='25.00' and order['confirmacion']=='confirmada'
    check('Compra real en QA: identidad y total no manipulables')
    with cursor_db() as cur:
        cur.execute('SELECT usuario_id,total,s3_comprobante_key FROM pedidos WHERE id=%s',(order['pedido_id'],))
        stored=cur.fetchone()
        assert stored['usuario_id']==a['id'] and str(stored['total'])=='25.00' and stored['s3_comprobante_key']
        cur.execute('SELECT stock FROM productos WHERE id=%s',(product,))
        assert cur.fetchone()['stock']==1
    check('Pedido persistido, stock descontado y comprobante vinculado')
    receipt=request('GET',f'/pedidos/{order["pedido_id"]}/comprobante',token=a['token'])
    assert str(order['pedido_id']) in receipt.text and len(receipt.content)>50
    assert cliente_s3().head_object(Bucket=os.environ['S3_BUCKET'],Key=stored['s3_comprobante_key'])['ServerSideEncryption']=='AES256'
    check('Comprobante descargable y cifrado AES256 en S3')
    assert request('GET','/pedidos',token=b['token']).json()['pedidos']==[]
    request('POST',f'/pedidos/{order["pedido_id"]}/reenviar-confirmacion',403,token=b['token'])
    request('GET',f'/pedidos/{order["pedido_id"]}/comprobante',404,token=b['token'])
    check('Otro usuario no lista, descarga ni reenvía el pedido ajeno')
    request('POST',f'/pedidos/{order["pedido_id"]}/reenviar-confirmacion',token=a['token'])
    check('El propietario sí puede regenerar su confirmación')
    request('POST','/ordenes/checkout',400,token=a['token'],json={'correo':prefix+'@example.invalid','items':items})
    with cursor_db() as cur:
        cur.execute('SELECT COUNT(*) AS n FROM pedidos WHERE usuario_id=%s',(a['id'],))
        assert cur.fetchone()['n']==1
        cur.execute('SELECT stock FROM productos WHERE id=%s',(product,))
        assert cur.fetchone()['stock']==1
    check('Sin sobreventa: compra rechazada no deja pedido parcial ni descuenta stock')
    print(json.dumps({'status':'PASS','checks':len(checks),'test_user_ids':[u['id'] for u in users],'test_product_id':product,'test_order_ids':order_ids}),flush=True)
finally:
    ids=[u['id'] for u in users]
    if ids:
        with cursor_db() as cur:
            cur.execute('SELECT id,usuario FROM usuarios WHERE id=ANY(%s)',(ids,))
            assert all(u['usuario'].startswith(prefix+'_') for u in cur.fetchall()), 'Fixture ownership check failed'
            cur.execute('SELECT id,s3_comprobante_key FROM pedidos WHERE usuario_id=ANY(%s)',(ids,))
            for row in cur.fetchall():
                key=row['s3_comprobante_key']
                if key:
                    assert key==f'comprobantes/pedido_{row["id"]}.txt'
                    cliente_s3().delete_object(Bucket=os.environ['S3_BUCKET'],Key=key)
            cur.execute('DELETE FROM pedidos WHERE usuario_id=ANY(%s)',(ids,))
            if product:
                cur.execute('DELETE FROM productos WHERE id=%s AND nombre=%s',(product,prefix+'_producto'))
            cur.execute('DELETE FROM usuarios WHERE id=ANY(%s)',(ids,))
        print('CLEANUP: eliminados únicamente los usuarios, producto, pedido y comprobante creados por esta prueba.',flush=True)
