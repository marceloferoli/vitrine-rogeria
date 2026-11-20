import os, uuid
from supabase import create_client, Client

class ProdutoService:
    def __init__(self):
        self.client: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
        self.bucket = "cosmeticos"

    def listar_ativos(self, marca: str = None):
        q = self.client.table("produtos").select("*").eq("ativo", True)
        if marca and marca != "Todas":
            q = q.eq("marca", marca)
        return q.order("destaque_dia", desc=True).order("criado_em", desc=True).execute().data

    def listar_todos_admin(self):
        return self.client.table("produtos").select("*").order("criado_em", desc=True).execute().data

    def upload_imagem(self, arquivo) -> str:
        ext = os.path.splitext(arquivo.filename)[1].lower() or ".jpg"
        nome = f"{uuid.uuid4().hex}{ext}"
        self.client.storage.from_(self.bucket).upload(path=nome, file=arquivo.read(), file_options={"content-type": arquivo.mimetype})
        return self.client.storage.from_(self.bucket).get_public_url(nome)

    def cadastrar(self, dados: dict, arquivo_imagem):
        url = self.upload_imagem(arquivo_imagem)
        novo = {
            "marca": dados["marca"], "nome": dados["nome"], "descricao": dados.get("descricao", ""),
            "preco_original": float(dados["preco_original"]) if dados.get("preco_original") else None,
            "preco_promocional": float(dados["preco_promocional"]), "imagem_url": url,
            "destaque_dia": bool(dados.get("destaque_dia")), "ativo": True
        }
        return self.client.table("produtos").insert(novo).execute()

    def alternar_status(self, pid: int, campo: str, atual: bool):
        return self.client.table("produtos").update({campo: not atual}).eq("id", pid).execute()

    def excluir(self, pid: int):
        return self.client.table("produtos").delete().eq("id", pid).execute()
