import os
import psycopg2
from werkzeug.security import generate_password_hash

DB_HOST = os.getenv("DB_HOST", "marketplace-db.cztatesqbrvy.us-east-1.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "dbadmin")
DB_PASS = os.getenv("DB_PASSWORD", os.getenv("DB_PASSWORD", ""))

print(f"[*] Conectando a RDS PostgreSQL en {DB_HOST}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=5432,
        connect_timeout=5
    )
    cur = conn.cursor()

    # 1. Tabla de usuarios con password_hash (Cero contraseñas en texto plano)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        usuario VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabla de productos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        precio NUMERIC(10,2) NOT NULL,
        stock INT NOT NULL
    );
    """)

    # 3. Tabla de pedidos (Persistencia real requerida por el parche)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id SERIAL PRIMARY KEY,
        usuario_id INT REFERENCES usuarios(id),
        correo_comprador VARCHAR(120) NOT NULL,
        total NUMERIC(10,2) NOT NULL,
        detalle TEXT NOT NULL,
        s3_comprobante_key VARCHAR(255),
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Insertar usuario inicial si no existe
    cur.execute("SELECT id FROM usuarios WHERE usuario = 'cesar_eval';")
    if not cur.fetchone():
        seed_password = os.environ.get("SEED_USER_PASSWORD", "")
        if len(seed_password) < 12:
            raise ValueError("Define SEED_USER_PASSWORD con al menos 12 caracteres para crear el usuario inicial.")
        hash_pass = generate_password_hash(seed_password)
        cur.execute("INSERT INTO usuarios (usuario, password_hash) VALUES (%s, %s);", ("cesar_eval", hash_pass))
        print("  [+] Usuario inicial 'cesar_eval' creado con hash criptografico.")

    # Insertar productos iniciales si la tabla esta vacia
    cur.execute("SELECT COUNT(*) FROM productos;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO productos (id, nombre, precio, stock) VALUES
        (1, 'Teclado Mecanico', 75.0, 10),
        (2, 'Mouse Inalambrico', 45.0, 25),
        (3, 'Monitor 24 pulg', 180.0, 5);
        """)
        print("  [+] Productos iniciales insertados en la base de datos.")

    # Insertar pedido de prueba #1001 si no existe
    cur.execute("SELECT id FROM pedidos WHERE id = 1001;")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO pedidos (id, usuario_id, correo_comprador, total, detalle, s3_comprobante_key)
        VALUES (1001, 1, 'cliente_prueba@dominio.com', 75.0, 'Teclado Mecanico x1', 'comprobantes/pedido_1001.txt');
        """)
        print("  [+] Pedido #1001 inicial creado con éxito en RDS.")

    conn.commit()
    cur.close()
    conn.close()
    print("[OK] Tablas de PostgreSQL creadas y pobladas exitosamente en AWS RDS.")

except Exception as e:
    print(f"[ERROR] Error conectando a RDS: {e}")
