import psycopg2
import boto3

# 1. Leer variables de entorno locales
env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

# 2. Consultar la relacion real en AWS RDS (PostgreSQL)
print("=" * 65)
print(" 1. CONSULTA RELACIONAL EN AWS RDS (USUARIOS + PEDIDOS)")
print("=" * 65)
conn = psycopg2.connect(
    host=env["DB_HOST"],
    dbname=env["DB_NAME"],
    user=env["DB_USER"],
    password=env["DB_PASSWORD"],
    port=5432
)
cur = conn.cursor()
cur.execute("""
    SELECT p.id, u.usuario, p.correo_comprador, p.total, p.detalle
    FROM pedidos p
    JOIN usuarios u ON p.usuario_id = u.id;
""")
for p in cur.fetchall():
    print(f"Pedido #{p[0]} | Cliente: {p[1]} | Correo: {p[2]} | Total: ${p[3]} | Item: {p[4]}")
cur.close()
conn.close()

# 3. Subir comprobante real a AWS S3 con cifrado AES-256
print("\n" + "=" * 65)
print(" 2. SUBIENDO COMPROBANTE REAL A AWS S3")
print("=" * 65)
bucket = "marketplace-datos-protegidos-cesar-lsca2314"
s3 = boto3.client("s3", region_name="us-east-1")

key = "comprobantes/pedido_1001.txt"
contenido = (
    "COMPROBANTE OFICIAL MARKETPLACE\n"
    "Pedido: #1001\n"
    "Cliente: cesar_eval\n"
    "Total: $75.00 USD\n"
    "Estado: REGISTRADO EN RDS POSTGRESQL\n"
)

s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=contenido.encode("utf-8"),
    ServerSideEncryption="AES256"
)
print(f"[OK] Archivo subido con exito a s3://{bucket}/{key}")
# 4. Listar objetos actuales en S3
print("\n--- OBJETOS ACTUALES EN TU BUCKET S3 ---")
resp = s3.list_objects_v2(Bucket=bucket)
for obj in resp.get("Contents", []):
    nombre = obj["Key"]
    tamano = obj["Size"]
    fecha = obj["LastModified"]
    print(f" -> {nombre} ({tamano} bytes) - Modificado: {fecha}")
print("=" * 65)
