from bedrock_vision import normalize_assessment

def test_pipe_category_not_displayed_as_classification():
    data = normalize_assessment({"battery_form":"pouch", "overall":"possible_visual_issue", "findings":[{"category":"residue|corrosion_like|casing_damage|possible_deformation|other", "evidence":"Visible powder on the surface", "location":"left side", "certainty":"confirmed"}]})
    assert data['findings'][0]['category'] == 'other'
    assert data['findings'][0]['certainty'] == 'uncertain'

def test_valid_deformation_kept():
    data = normalize_assessment({"battery_form":"pouch", "overall":"possible_visual_issue", "findings":[{"category":"possible_deformation", "evidence":"The pouch is visibly bulging", "location":"center", "certainty":"possible"}]})
    assert data['findings'][0]['category'] == 'possible_deformation'

def test_unsupported_findings_dropped():
    data = normalize_assessment({"overall":"possible_visual_issue", "findings":[{"category":"residue", "evidence":"powder"}]})
    assert not data['findings']
    assert data['overall'] == 'insufficient_evidence'
