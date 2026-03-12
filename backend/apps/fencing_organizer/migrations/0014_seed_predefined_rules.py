# Generated data migration for seeding predefined rules

from django.db import migrations


def seed_predefined_data(apps, schema_editor):
    """
    Seed elimination types, ranking types, and predefined rules.
    """
    EliminationType = apps.get_model('fencing_organizer', 'DjangoEliminationType')
    RankingType = apps.get_model('fencing_organizer', 'DjangoRankingType')
    Rule = apps.get_model('fencing_organizer', 'DjangoRule')

    # Create Elimination Types
    elimination_types_data = [
        {'type_code': 'SINGLE_ELIMINATION', 'display_name': '单败淘汰赛'},
        {'type_code': 'DOUBLE_ELIMINATION', 'display_name': '双败淘汰赛'},
        {'type_code': 'ROUND_ROBIN_ONLY', 'display_name': '仅循环赛'},
    ]

    elimination_types = {}
    for et_data in elimination_types_data:
        et, created = EliminationType.objects.get_or_create(
            type_code=et_data['type_code'],
            defaults={'display_name': et_data['display_name']}
        )
        elimination_types[et.type_code] = et

    # Create Ranking Types
    ranking_types_data = [
        {'type_code': 'BRONZE_MATCH', 'display_name': '铜牌赛'},
        {'type_code': 'NO_BRONZE', 'display_name': '无铜牌赛'},
    ]

    ranking_types = {}
    for rt_data in ranking_types_data:
        rt, created = RankingType.objects.get_or_create(
            type_code=rt_data['type_code'],
            defaults={'display_name': rt_data['display_name']}
        )
        ranking_types[rt.type_code] = rt

    # Create Predefined Rules
    predefined_rules_data = [
        {
            'rule_name': 'World Cup',
            'preset_code': 'world_cup',
            'is_preset': True,
            'stages_config': [
                {
                    'type': 'pool',
                    'config': {
                        'byes': 16,
                        'hits': 5,
                        'elimination_rate': 20
                    }
                },
                {
                    'type': 'de',
                    'config': {
                        'hits': 15,
                        'final_stage': 'bronze_medal',
                        'rank_to': 8
                    }
                }
            ],
            'elimination_type_code': 'SINGLE_ELIMINATION',
            'final_ranking_type_code': 'BRONZE_MATCH',
            'pool_size': 7,
            'total_qualified_count': 64,
            'match_score_pool': 5,
            'match_score_elimination': 15,
            'group_qualification_ratio': 0.80,
            'description': 'FIE World Cup format: Pool round followed by single elimination with bronze medal match'
        },
        {
            'rule_name': 'Olympics',
            'preset_code': 'olympics',
            'is_preset': True,
            'stages_config': [
                {
                    'type': 'de',
                    'config': {
                        'hits': 15,
                        'final_stage': 'bronze_medal',
                        'rank_to': 8
                    }
                }
            ],
            'elimination_type_code': 'SINGLE_ELIMINATION',
            'final_ranking_type_code': 'BRONZE_MATCH',
            'pool_size': None,
            'total_qualified_count': 64,
            'match_score_pool': None,
            'match_score_elimination': 15,
            'group_qualification_ratio': None,
            'description': 'Olympic format: Direct single elimination with bronze medal match'
        }
    ]

    for rule_data in predefined_rules_data:
        Rule.objects.get_or_create(
            preset_code=rule_data['preset_code'],
            defaults={
                'rule_name': rule_data['rule_name'],
                'is_preset': rule_data['is_preset'],
                'stages_config': rule_data['stages_config'],
                'elimination_type': elimination_types[rule_data['elimination_type_code']],
                'final_ranking_type': ranking_types[rule_data['final_ranking_type_code']],
                'pool_size': rule_data['pool_size'],
                'total_qualified_count': rule_data['total_qualified_count'],
                'match_score_pool': rule_data['match_score_pool'],
                'match_score_elimination': rule_data['match_score_elimination'],
                'group_qualification_ratio': rule_data['group_qualification_ratio'],
                'description': rule_data['description'],
            }
        )


def reverse_seed(apps, schema_editor):
    """
    Reverse migration: delete seeded data.
    """
    Rule = apps.get_model('fencing_organizer', 'DjangoRule')
    RankingType = apps.get_model('fencing_organizer', 'DjangoRankingType')
    EliminationType = apps.get_model('fencing_organizer', 'DjangoEliminationType')

    Rule.objects.filter(preset_code__in=['world_cup', 'olympics']).delete()
    RankingType.objects.filter(type_code__in=['BRONZE_MATCH', 'NO_BRONZE']).delete()
    EliminationType.objects.filter(type_code__in=['SINGLE_ELIMINATION', 'DOUBLE_ELIMINATION', 'ROUND_ROBIN_ONLY']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fencing_organizer', '0013_add_rule_stages_and_custom_config'),
    ]

    operations = [
        migrations.RunPython(seed_predefined_data, reverse_seed),
    ]
