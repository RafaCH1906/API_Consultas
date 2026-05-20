import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
db_url = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}?sslmode=require"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

# Crear 5000 registros de prueba
print("Creando 5000 registros...")
values = []
for i in range(5000):
    values.append((
        f"2000{i:07d}", f"EMPRESA PRUEBA {i}", "ACTIVO", "HABIDO",
        None, None, None, None, None, None, None, None, None, None, None, None, "", ""
    ))

print("Limpiando previos...")
with engine.connect() as conn:
    conn.execute(text("DELETE FROM ruc WHERE numero_documento LIKE '20000000%%'"))
    conn.commit()

print("Probando execute_values de psycopg2...")
db = SessionLocal()
try:
    start = time.time()
    # Obtener conexion nativa de psycopg2
    raw_conn = db.connection().connection
    cursor = raw_conn.cursor()
    
    query = """
    INSERT INTO ruc (numero_documento, nombre, estado, condicion, ubigeo, via_tipo, via_nombre, zona_codigo, zona_tipo, numero, interior, lote, departamento, manzana, kilometro, direccion, distrito, provincia)
    VALUES %s
    """
    execute_values(cursor, query, values)
    db.commit()
    print(f"¡Éxito con execute_values! 5000 registros insertados en {time.time() - start:.2f} segundos.")
except Exception as e:
    print("Error:", e)
finally:
    db.close()
