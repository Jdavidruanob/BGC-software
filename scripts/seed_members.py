"""
Carga masiva de los 54 socios fundadores del BGC.
Ejecutar una sola vez en la DB objetivo cuando no estén cargados.
Uso: python scripts/seed_members.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.connection import DBConnection
from db.repositories.socios_repo import SociosRepository
from config import DB_PATH_FINAL


DEFAULT_PHOTO = "assets/photos/default_user.png"

SOCIOS_DATA = [
    ("Alvaro Lizardo", "Burbano Garcia", "3113661423", 12563000),
    ("Maritza Del S.", "Padilla Jojoa", "3168086883", 14310000),
    ("Nathalia Soledad", "Burbano Padilla", "3103819933", 861000),
    ("Jose David", "Ruano Burbano", "3116426370", 5580000),
    ("Julieta", "Hoyos Burbano", "", 6392700),
    ("Karoll Marcela", "Burbano Padilla", "3122133604", 7688400),
    ("William David", "Jimenez Padilla", "3015673059", 792500),
    ("Renata", "Jimenez Burbano", "", 4991000),
    ("Isabel Cecilia", "Jojoa", "", 4282000),
    ("Teresa de Jesús", "Padilla Jojoa", "3003193120", 2170800),
    ("Francisco Wilson", "Padilla Jojoa", "3226845657", 1437900),
    ("Fanny Patricia", "Padilla Jojoa", "3146902065", 8537550),
    ("Sonnia Mabel", "Padilla Jojoa", "3173188813", 8074120),
    ("Samuel Alejandro", "Jimenez Padill", "", 14118652),
    ("Miguel Zenon", "Burbano Rosero", "", 2729000),
    ("Soledad Del Carmen", "García Castro", "", 21223000),
    ("Magally Del Socorro", "Burbano García", "3205636149", 11244000),
    ("Gladys Nayleth", "Burbano García", "3103690615", 1330000),
    ("Fabio", "Ayala Burbano", "", 237800),
    ("Luz Marina", "Burbano García", "", 14629386),
    ("Zenon Efraín", "Burbano García", "3166315709", 1937150),
    ("Manuel Alejandro", "Burbano Del Castillo", "3153954016", 733700),
    ("Ana Nereyda", "Burbano García", "3136887622", 9442501),
    ("Javier Mauricio", "Castro Burbano", "3008632365", 1813600),
    ("Ayda Balbina", "Burbano García", "3015521454", 14327000),
    ("Angela María", "Moreno Burbano", "", 11899000),
    ("Luisa María", "Delgado Burbano", "", 386000),
    ("Gabriel Andrés", "Chamorro Burbano", "3103610370", 905760),
    ("Gabriela Soledad", "Chamorro Rosero", "", 781000),
    ("Mariangel", "Chamorro Rosero", "", 138000),
    ("Rodrigo", "García Castro", "3103335195", 5975000),
    ("Jesús Rodrigo", "García Delgado", "3137393236", 11357790),
    ("Ana Milena", "García Delgado", "3215717115", 6707500),
    ("María Guadalupe", "Díaz García", "", 1450000),
    ("Harvey", "García Luna", "3205758365", 1789530),
    ("Marcela", "Salazar Florez", "3122950250", 1789530),
    ("Isabella", "García Salazar", "3204513773", 24500000),
    ("Mariana", "García Salazar", "3104271355", 17260000),
    ("Luz Alba", "Florez Rosero", "", 5154800),
    ("Siomara Alejandra", "García Luna", "3123518275", 5121760),
    ("José Manuel", "Narváez", "", 3247000),
    ("Olga Patricia", "Toro Melo", "3122150867", 9730236),
    ("Heyman Gerardo", "Luna Toro", "3123748909", 2469600),
    ("Angie Daniela", "Luna Toro", "", 1100000),
    ("Vianey", "Luna Toro", "", 1100000),
    ("Magceider", "García Luna", "3227002755", 4990000),
    ("Pilar", "Herrera Escalante", "3214170501", 380000),
    ("Michael", "García Herrera", "", 1280000),
    ("Katalina", "García Herrera", "", 650000),
    ("Ruth Amparo", "Florez Castro", "3147015008", 14050000),
    ("Miguel Andrés", "Vallejo Florez", "3163204109", 5550000),
    ("Noe Angel", "Guachavez", "3136076022", 16700000),
    ("Alicia", "Florez Castro", "3106940863", 9900000),
    ("Luis Fernando", "Vallejos Florez", "3117984000", 16250000),
]


def run(db_path=None):
    path = db_path or DB_PATH_FINAL
    db = DBConnection(path)
    if not db.connect():
        print("❌ No se pudo conectar a la base de datos.")
        return
    repo = SociosRepository(db)
    print(f"\n🚀 Iniciando carga de {len(SOCIOS_DATA)} socios...\n")
    for nombres, apellidos, celular, saldo in SOCIOS_DATA:
        repo.save(nombres=nombres, apellidos=apellidos, phone=celular,
                  photo_path=DEFAULT_PHOTO, saldo=saldo)
    print(f"\n✅ Carga masiva finalizada. {len(SOCIOS_DATA)} socios procesados.")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
