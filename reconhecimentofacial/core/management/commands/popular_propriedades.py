"""
Comando Django para popular o banco de dados com 30 propriedades rurais
com diferentes níveis de acesso (1, 2 e 3).

Uso: python manage.py popular_propriedades
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import PropriedadeRural
from decimal import Decimal
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Popula o banco de dados com 30 propriedades rurais com diferentes níveis de impacto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todas as propriedades antes de criar novas',
        )

    def handle(self, *args, **options):
        # Se a flag --limpar for passada, remove todas as propriedades
        if options['limpar']:
            count = PropriedadeRural.objects.all().count()
            PropriedadeRural.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'🗑️  {count} propriedades removidas do banco de dados')
            )

        # Verificar se existe pelo menos um usuário para associar
        usuario = User.objects.first()
        if not usuario:
            self.stdout.write(
                self.style.ERROR('❌ Nenhum usuário encontrado. Crie um usuário primeiro!')
            )
            return

        # Lista de estados brasileiros
        estados = ['SP', 'MG', 'RJ', 'BA', 'RS', 'PR', 'SC', 'GO', 'MS', 'MT', 'PA', 'AM', 'TO']
        
        # Lista de cidades brasileiras
        cidades = [
            'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Porto Alegre',
            'Curitiba', 'Florianópolis', 'Goiânia', 'Campo Grande', 'Cuiabá',
            'Belém', 'Manaus', 'Palmas', 'Brasília', 'Vitória'
        ]
        
        # Lista de agrotóxicos proibidos (exemplos)
        agrotoxicos = [
            'Paraquat', 'Carbofurano', 'Endossulfan', 'Metamidofós', 'Aldicarbe',
            'Forato', 'Parationa Metílica', 'Monocrotofós', 'Triclorfom', 'DDT',
            'Aldrin', 'Dieldrin', 'Heptacloro', 'Mirex', 'Clordano'
        ]
        
        # Nomes de propriedades
        nomes_fazendas = [
            'Fazenda Santa Maria', 'Sítio Boa Vista', 'Fazenda São José',
            'Rancho Alegre', 'Fazenda Primavera', 'Sítio Paraíso',
            'Fazenda Esperança', 'Chácara Nova Vida', 'Fazenda Monte Verde',
            'Sítio Recanto Verde', 'Fazenda Bela Vista', 'Rancho do Sol',
            'Fazenda Campo Limpo', 'Sítio Água Clara', 'Fazenda Três Irmãos',
            'Estância São Pedro', 'Fazenda Serra Azul', 'Sítio Flor do Campo',
            'Fazenda Vale Verde', 'Rancho Feliz', 'Fazenda Ribeirão',
            'Sítio Girassol', 'Fazenda Palmeiras', 'Chácara do Lago',
            'Fazenda Horizonte', 'Sítio Pôr do Sol', 'Fazenda Alvorada',
            'Rancho Grande', 'Fazenda Rio Claro', 'Sítio Ventania'
        ]
        
        # Nomes de proprietários
        nomes = [
            'João Silva', 'Maria Santos', 'Carlos Oliveira', 'Ana Costa',
            'Pedro Almeida', 'Juliana Ferreira', 'Roberto Souza', 'Fernanda Lima',
            'Marcos Pereira', 'Patrícia Rodrigues', 'José Martins', 'Carla Mendes',
            'Antonio Barbosa', 'Lucia Cardoso', 'Paulo Ribeiro', 'Sandra Araújo',
            'Ricardo Gomes', 'Beatriz Castro', 'Fernando Dias', 'Cristina Moreira',
            'Luiz Cunha', 'Márcia Correia', 'Eduardo Teixeira', 'Renata Pinto',
            'Francisco Ramos', 'Gabriela Vieira', 'André Monteiro', 'Camila Freitas',
            'Rafael Carvalho', 'Adriana Nunes'
        ]
        
        # Descrições de impacto por nível
        descricoes_nivel_1 = [
            'Contaminação leve detectada em análises pontuais do lençol freático. Necessário monitoramento.',
            'Presença de resíduos em baixa concentração próximo à área de plantio.',
            'Impacto localizado com potencial de recuperação natural em médio prazo.',
        ]
        
        descricoes_nivel_2 = [
            'Contaminação moderada dos recursos hídricos com afetação de córregos próximos.',
            'Presença significativa de resíduos químicos em análises do solo e água subterrânea.',
            'Impacto sobre fauna aquática local, com redução da biodiversidade observada.',
        ]
        
        descricoes_nivel_3 = [
            'Contaminação severa com comprometimento de rios principais da região.',
            'Alto índice de toxicidade detectado em múltiplos pontos de coleta, afetando comunidades ribeirinhas.',
            'Impacto crítico em ecossistemas aquáticos com mortandade de peixes e comprometimento de aquíferos.',
        ]

        self.stdout.write(self.style.SUCCESS('🌱 Iniciando cadastro de 30 propriedades...'))
        self.stdout.write('')

        propriedades_criadas = 0
        
        # Criar 10 propriedades de cada nível (1, 2 e 3)
        for nivel in [1, 2, 3]:
            self.stdout.write(f'📊 Criando 10 propriedades de Nível {nivel}...')
            
            for i in range(10):
                idx = (nivel - 1) * 10 + i
                
                # Selecionar descrição baseada no nível
                if nivel == 1:
                    descricao = random.choice(descricoes_nivel_1)
                elif nivel == 2:
                    descricao = random.choice(descricoes_nivel_2)
                else:
                    descricao = random.choice(descricoes_nivel_3)
                
                # Gerar CPF/CNPJ fictício
                if random.choice([True, False]):
                    # CPF: 000.000.000-00
                    cpf_cnpj = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
                else:
                    # CNPJ: 00.000.000/0000-00
                    cpf_cnpj = f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/{random.randint(1000, 9999)}-{random.randint(10, 99)}"
                
                # Gerar coordenadas geográficas (Brasil)
                latitude = Decimal(str(random.uniform(-33.75, 5.27))).quantize(Decimal('0.000001'))
                longitude = Decimal(str(random.uniform(-73.99, -34.79))).quantize(Decimal('0.000001'))
                
                # Área em hectares (varia conforme o nível)
                if nivel == 1:
                    area = Decimal(str(random.uniform(10, 100))).quantize(Decimal('0.01'))
                elif nivel == 2:
                    area = Decimal(str(random.uniform(100, 500))).quantize(Decimal('0.01'))
                else:
                    area = Decimal(str(random.uniform(500, 2000))).quantize(Decimal('0.01'))
                
                # Data de identificação (últimos 2 anos)
                dias_atras = random.randint(0, 730)
                data_identificacao = datetime.now().date() - timedelta(days=dias_atras)
                
                # Criar a propriedade
                propriedade = PropriedadeRural.objects.create(
                    nome_propriedade=nomes_fazendas[idx],
                    proprietario=nomes[idx],
                    cpf_cnpj=cpf_cnpj,
                    endereco=f"Rodovia {random.choice(['BR', 'SP', 'MG'])}-{random.randint(100, 999)}, Km {random.randint(1, 200)}",
                    cidade=random.choice(cidades),
                    estado=random.choice(estados),
                    area_hectares=area,
                    agrotoxico_utilizado=random.choice(agrotoxicos),
                    nivel_impacto=nivel,
                    descricao_impacto=descricao,
                    data_identificacao=data_identificacao,
                    latitude=latitude,
                    longitude=longitude,
                    usuario_cadastro=usuario,
                    ativo=True
                )
                
                propriedades_criadas += 1
                
                # Feedback visual a cada 5 propriedades
                if propriedades_criadas % 5 == 0:
                    self.stdout.write(f'  ✓ {propriedades_criadas}/30 propriedades criadas')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'✅ SUCESSO! {propriedades_criadas} propriedades cadastradas!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Resumo por nível
        self.stdout.write('📈 Resumo por Nível de Impacto:')
        for nivel in [1, 2, 3]:
            count = PropriedadeRural.objects.filter(nivel_impacto=nivel).count()
            nivel_nome = dict(PropriedadeRural.NIVEL_CHOICES)[nivel]
            emoji = '🟢' if nivel == 1 else '🟡' if nivel == 2 else '🔴'
            self.stdout.write(f'  {emoji} {nivel_nome}: {count} propriedades')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Banco de dados populado com sucesso!'))
        self.stdout.write(self.style.WARNING('💡 Dica: Use --limpar para remover todas antes de criar novas'))
