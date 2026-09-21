"""
Suíte de Testes de Integridade PBIP & TMDL (Fabric Semantic Model & Report Authoring)

Proposta:
Valida a integridade sintática e semântica dos arquivos do projeto Power BI (PBIP) Isolacao Motores,
garantindo que alterações em arquivos TMDL e PBIR respeitem as diretrizes oficiais
das skills `powerbi-report-authoring` e `semantic-model-authoring`.

Cenários cobertos:
- Balanceamento estrito de blocos de código DAX (delimitadores ```) em arquivos TMDL.
- Ausência de conflitos de merge Git (<<<<<<<, =======, >>>>>>>).
- Proibição de dataType explícito em medidas (Analysis Services infere automaticamente).
- Unicidade global de nomes de medidas.
- Validação estrutural de todos os arquivos JSON do relatório PBIR.
- Consistência do vínculo relativo entre .Report e .SemanticModel em definition.pbir.

Como executar isoladamente:
    pytest tests/test_pbip_integrity.py -v
"""

import glob
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMANTIC_MODEL_DIR = os.path.join(BASE_DIR, "isolacao.SemanticModel")
REPORT_DIR = os.path.join(BASE_DIR, "isolacao.Report")

GIT_CONFLICT_PATTERN = re.compile(r"^(<{7}\s|={7}\s*$|>{7}\s)", re.MULTILINE)


def test_definition_pbir_relative_link():
    """Valida se definition.pbir aponta para o SemanticModel no mesmo nível relativo."""
    pbir_file = os.path.join(REPORT_DIR, "definition.pbir")
    assert os.path.exists(pbir_file), f"Arquivo definition.pbir não encontrado em {pbir_file}"

    with open(pbir_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset_ref = data.get("datasetReference", {})
    by_path = dataset_ref.get("byPath", {})
    path_val = by_path.get("path")
    assert path_val is not None, "definition.pbir não possui campo datasetReference.byPath.path"

    target_semantic_dir = os.path.normpath(os.path.join(REPORT_DIR, path_val))
    assert os.path.exists(target_semantic_dir), (
        f"Caminho do SemanticModel referenciado em definition.pbir não existe: {target_semantic_dir}"
    )


def test_tmdl_syntax_and_balance():
    """Valida balanceamento de blocos de código DAX e ausência de conflitos de merge em arquivos TMDL."""
    tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "definition", "**", "*.tmdl"), recursive=True)
    assert len(tmdl_files) > 0, "Nenhum arquivo TMDL encontrado no modelo semântico!"

    errors = []
    for fpath in tmdl_files:
        rel_path = os.path.relpath(fpath, BASE_DIR)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Conflitos de merge
        if GIT_CONFLICT_PATTERN.search(content):
            errors.append(f"{rel_path}: Conflito de merge Git detectado!")

        # Balanceamento de ```
        backtick_count = len(re.findall(r"```", content))
        if backtick_count % 2 != 0:
            errors.append(f"{rel_path}: Quantidade ímpar de blocos de crase tripla (```) detectada ({backtick_count}).")

    assert not errors, "Erros encontrados nos arquivos TMDL:\n" + "\n".join(errors)


def test_measure_uniqueness_and_no_explicit_datatype():
    """Valida que medidas não possuem dataType explícito (regra Fabric) e possuem nomes únicos."""
    tmdl_tables_dir = os.path.join(SEMANTIC_MODEL_DIR, "definition", "tables")
    if not os.path.exists(tmdl_tables_dir):
        return  # Nenhuma tabela criada ainda

    table_files = glob.glob(os.path.join(tmdl_tables_dir, "*.tmdl"))

    all_measures = {}
    errors = []

    for fpath in table_files:
        table_name = os.path.basename(fpath).replace(".tmdl", "")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extrair medidas declaradas
        parts = re.split(r"\n\tmeasure\s+", content)
        for p in parts[1:]:
            header_end = p.find("=")
            if header_end == -1:
                continue
            measure_name = p[:header_end].strip().strip("'")

            # Verificar se já existe medida com esse nome
            if measure_name in all_measures:
                errors.append(
                    f"Medida duplicada: [{measure_name}] declarada em '{table_name}' e '{all_measures[measure_name]}'"
                )
            else:
                all_measures[measure_name] = table_name

            # Verificar se foi definido dataType na medida
            body_until_next = p[header_end + 1 :]
            for line in body_until_next.splitlines():
                if re.match(r"^\t(?:column|partition|measure)\b", line):
                    break
                if re.match(r"^\tdataType:\s*", line):
                    errors.append(
                        f"Medida [{measure_name}] em '{table_name}' define dataType explícito. "
                        "O Analysis Services infere automaticamente."
                    )

    assert not errors, "Erros nas medidas do modelo semântico:\n" + "\n".join(errors)


def test_pbir_json_validity():
    """Valida que todos os arquivos JSON do relatório PBIR são válidos e bem-formados."""
    json_files = glob.glob(os.path.join(REPORT_DIR, "definition", "**", "*.json"), recursive=True)
    assert len(json_files) > 0, "Nenhum arquivo JSON de definição de relatório PBIR encontrado!"

    invalid_jsons = []
    for jpath in json_files:
        rel_path = os.path.relpath(jpath, BASE_DIR)
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            invalid_jsons.append(f"{rel_path}: Erro de parse JSON ({e})")

    assert not invalid_jsons, "Arquivos JSON inválidos no relatório PBIR:\n" + "\n".join(invalid_jsons)


def test_pages_and_visuals_hierarchy():
    """Valida que todas as páginas contêm page.json e que visuais possuem estrutura válida."""
    pages_dir = os.path.join(REPORT_DIR, "definition", "pages")
    if not os.path.exists(pages_dir):
        return  # Relatório sem páginas ainda

    page_dirs = [d for d in glob.glob(os.path.join(pages_dir, "*")) if os.path.isdir(d)]
    errors = []
    for pdir in page_dirs:
        p_json = os.path.join(pdir, "page.json")
        if not os.path.exists(p_json):
            errors.append(f"Página sem page.json: {os.path.basename(pdir)}")

        visuals_dir = os.path.join(pdir, "visuals")
        if os.path.exists(visuals_dir):
            for vdir in glob.glob(os.path.join(visuals_dir, "*")):
                v_json = os.path.join(vdir, "visual.json")
                if not os.path.exists(v_json):
                    errors.append(
                        f"Visual sem visual.json: {os.path.basename(vdir)} na página {os.path.basename(pdir)}"
                    )

    assert not errors, "Inconsistências na hierarquia de páginas e visuais:\n" + "\n".join(errors)
