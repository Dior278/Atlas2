from aparte.workspace.config import load_product


def test_product_has_one_identity():
    product = load_product()
    assert product.project_id == "atlas"
    assert product.display_name == "Atlas2"
    assert product.companion_name == "Atlas"
    assert product.protocol_version == 12
