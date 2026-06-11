from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    key: str
    name: str
    category: str
    description: str

    @property
    def label(self) -> str:
        return f"{self.name} ({self.category})"


FUTUREMEDIA_PRODUCTS: tuple[Product, ...] = (
    Product(
        key="show-drones-locacao",
        name="Show de Drones",
        category="Locação",
        description="Espetáculo aéreo sincronizado para eventos, lançamentos e ativações de alto impacto.",
    ),
    Product(
        key="robo-troy-locacao",
        name="Robô Troy",
        category="Locação",
        description="Robô bípede para experiências de inovação, interação e impacto visual.",
    ),
    Product(
        key="robo-maximus-locacao",
        name="Robô Maximus",
        category="Locação",
        description="Robô de atendimento com interação, reconhecimento e funções de recepção.",
    ),
    Product(
        key="cao-scooby-locacao",
        name="Cão Robótico Scooby",
        category="Locação",
        description="Atração robótica para surpreender o público em ações promocionais e eventos.",
    ),
    Product(
        key="robo-buddy-locacao",
        name="Robô Buddy e Buddy Pro",
        category="Locação",
        description="Robôs de serviço para recepção, hospitalidade, marketing e interação com o público.",
    ),
    Product(
        key="robo-nik-locacao",
        name="Robô Nik",
        category="Locação",
        description="Robô para transporte de itens, atendimento e ativação em PDV ou restaurantes.",
    ),
    Product(
        key="robo-display-locacao",
        name="Robô Display",
        category="Locação",
        description="Robô interativo com tela, fala sincronizada e recursos para captação de leads.",
    ),
    Product(
        key="robo-spark-locacao",
        name="Robô Spark",
        category="Locação",
        description="Assistente inteligente e versátil para exibição de produtos e interação guiada.",
    ),
    Product(
        key="avatar-ia-locacao",
        name="Avatar IA",
        category="Locação",
        description="Guia digital para informações, perguntas frequentes e apoio ao visitante.",
    ),
    Product(
        key="totem-foto-ia-locacao",
        name="Totem Foto IA",
        category="Locação",
        description="Experiência com imagem e realidade aumentada para engajamento e lembrança de marca.",
    ),
    Product(
        key="espelho-interativo-locacao",
        name="Espelho Interativo",
        category="Locação",
        description="Espelho touch para fotos, interação, captação de leads e ativação de marca.",
    ),
    Product(
        key="parede-agilidade-locacao",
        name="Parede de Agilidade",
        category="Locação",
        description="Jogo interativo para estimular competição, fluxo no estande e atenção do público.",
    ),
    Product(
        key="grafite-digital-locacao",
        name="Grafite Digital",
        category="Locação",
        description="Experiência criativa para personalização de imagens com linguagem urbana e interativa.",
    ),
    Product(
        key="air-touch-locacao",
        name="Air Touch",
        category="Locação",
        description="Interação por movimentos das mãos para experiências sem contato físico.",
    ),
    Product(
        key="holograma-box-locacao",
        name="Holograma Box",
        category="Locação",
        description="Vitrine holográfica para apresentar produtos, pessoas ou mensagens com alto impacto.",
    ),
    Product(
        key="holograma-3d-locacao",
        name="Holograma 3D",
        category="Locação",
        description="Comunicação holográfica para merchandising e experiências visuais imersivas.",
    ),
    Product(
        key="promotora-holografica-locacao",
        name="Promotora Holográfica",
        category="Locação",
        description="Apresentadora holográfica para recepção, explicação e interação com o público.",
    ),
    Product(
        key="realidade-virtual-locacao",
        name="Realidade Virtual",
        category="Locação",
        description="Experiências imersivas em 360 graus, games e conteúdos sensoriais.",
    ),
    Product(
        key="cambot-locacao",
        name="CamBot",
        category="Locação",
        description="Braço robótico para produção de vídeos, vinhetas e conteúdo com efeito visual.",
    ),
    Product(
        key="braco-robotico-locacao",
        name="Braço Robótico",
        category="Locação",
        description="Equipamento programável para servir, apresentar produtos e criar impacto ao vivo.",
    ),
    Product(
        key="totens-telas-locacao",
        name="Totens e Telas Interativas",
        category="Locação",
        description="Solução completa de interação com aplicativos, jogos e conteúdo personalizado.",
    ),
    Product(
        key="robo-troy-venda",
        name="Robô Troy",
        category="Venda",
        description="Versão para aquisição do robô bípede com foco em uso recorrente e institucional.",
    ),
    Product(
        key="cao-scooby-venda",
        name="Cão Robótico Scooby",
        category="Venda",
        description="Atração robótica disponível para compra e uso contínuo em ativações.",
    ),
    Product(
        key="robo-buddy-venda",
        name="Robô Buddy",
        category="Venda",
        description="Robô de serviço para rotinas de recepção, hospitalidade e atendimento.",
    ),
    Product(
        key="robo-nik-venda",
        name="Robô Nik",
        category="Venda",
        description="Robô para transporte e apresentação de itens em operações permanentes.",
    ),
    Product(
        key="robo-nik-pro-venda",
        name="Robô Nik Pro",
        category="Venda",
        description="Versão avançada do Robô Nik para operações que exigem mais autonomia e presença.",
    ),
    Product(
        key="robo-spark-venda",
        name="Robô Spark",
        category="Venda",
        description="Assistente inteligente para apresentação, orientação e interação com dados.",
    ),
    Product(
        key="totens-interativos-venda",
        name="Totens Interativos",
        category="Venda",
        description="Totens para aplicações interativas, comunicação e experiências permanentes.",
    ),
)

PRODUCT_BY_KEY = {product.key: product for product in FUTUREMEDIA_PRODUCTS}
PRODUCT_BY_LABEL = {product.label: product for product in FUTUREMEDIA_PRODUCTS}


def products_by_category() -> dict[str, tuple[Product, ...]]:
    grouped: dict[str, list[Product]] = {}
    for product in FUTUREMEDIA_PRODUCTS:
        grouped.setdefault(product.category, []).append(product)
    return {category: tuple(items) for category, items in grouped.items()}


def get_product(key_or_label: str) -> Product | None:
    normalized = key_or_label.strip()
    return PRODUCT_BY_KEY.get(normalized) or PRODUCT_BY_LABEL.get(normalized)


def format_selected_products(selected: list[str] | None) -> str:
    if not selected:
        return "Nenhum produto selecionado."

    lines: list[str] = []
    for item in selected:
        product = get_product(item)
        if product:
            lines.append(f"- {product.label}: {product.description}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)

