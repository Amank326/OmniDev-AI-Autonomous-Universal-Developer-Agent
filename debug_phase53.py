from code_generator_service import *

reset_code_generation_service()
config = CodeGenerationConfig(
    language=LanguageType.PYTHON,
    code_type=CodeType.CLIENT,
    include_documentation=True,
    include_type_hints=True,
    include_error_handling=True
)

endpoints = [
    Endpoint(
        path='/complex/{id}/endpoint',
        method='POST',
        summary='Complex endpoint test',
        parameters=[
            Parameter(name='id', type_hint='str', location='path', required=True),
            Parameter(name='filter', type_hint='str', location='query', required=False)
        ],
        request_body={'type': 'object'},
        responses=[
            Response(status_code=200, content_type='application/json', schema={'type': 'object'}),
        ],
        tags=['complex']
    ),
]

generator = PythonCodeGenerator(config)
generated = generator.generate_client(endpoints)

for code in generated:
    if 'client' in code.filename:
        print('=== CLIENT CODE ===')
        print(code.content)
        print()
        print('=== CHECKS ===')
        print(f'Has except: {"except" in code.content}')
        print(f'Has raise: {"raise" in code.content}')
        print(f'Has try: {"try" in code.content}')
        print(f'Total length: {len(code.content)} chars')
