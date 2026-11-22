import re
import os, sys
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from models.produto_service import ProdutoService

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))
app.secret_key = os.environ.get("SECRET_KEY", "vitrine-dev")
service = ProdutoService()

@app.route("/")
def index():
    marca = request.args.get("marca", "Todas")
    produtos = service.listar_ativos(marca)
    whats_bruto = os.environ.get("WHATSAPP_NUMERO", "5538999999999")
    whats = re.sub(r"\D", "", whats_bruto)
    if len(whats) in (10, 11):
        whats = "55" + whats
    for p in produtos:
        msg = f"Olá Maria Rogéria! Tenho interesse em: *{p['nome']}* ({p['marca']}) por *R$ {p['preco_promocional']:.2f}*."
        p["link_whatsapp"] = f"https://wa.me/{whats}?text={quote(msg)}"
    return render_template("index.html", produtos=produtos, marca_selecionada=marca)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("senha") == os.environ.get("ADMIN_SENHA"):
            session["logado"] = True
            return redirect(url_for("admin"))
        flash("Senha incorreta!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logado"):
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            foto = request.files.get("imagem")
            if not foto or not foto.filename:
                flash("Selecione uma foto.", "warning")
                return redirect(url_for("admin"))
            service.cadastrar({
                "marca": request.form.get("marca"), "nome": request.form.get("nome"),
                "descricao": request.form.get("descricao"), "preco_original": request.form.get("preco_original"),
                "preco_promocional": request.form.get("preco_promocional"),
                "destaque_dia": request.form.get("destaque_dia") == "on"
            }, foto)
            flash("Oferta publicada!", "success")
        except Exception as e:
            flash(f"Erro: {e}", "danger")
        return redirect(url_for("admin"))
    return render_template("admin.html", produtos=service.listar_todos_admin())

@app.route("/admin/toggle/<int:id>/<campo>/<int:valor>")
def toggle(id, campo, valor):
    if not session.get("logado"): return redirect(url_for("login"))
    service.alternar_status(id, campo, bool(valor))
    return redirect(url_for("admin"))

@app.route("/admin/excluir/<int:id>")
def excluir(id):
    if not session.get("logado"): return redirect(url_for("login"))
    service.excluir(id)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
