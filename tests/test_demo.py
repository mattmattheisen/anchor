import json

from examples.run_anchor_demo import main


def test_demo_runs_and_emits_valid_json(capsys):
    main()

    captured = capsys.readouterr()

    output = captured.out.strip()

    assert output

    result = json.loads(output)

    assert isinstance(result, dict)
    assert result["schema_version"] == "1.0"
    assert "headline" in result
    assert "recommendation" in result
    assert "portfolio_posture" in result
    assert "selected_opportunities" in result


def test_demo_returns_three_selected_opportunities(capsys):
    main()

    captured = capsys.readouterr()

    result = json.loads(
        captured.out.strip()
    )

    assert len(
        result["selected_opportunities"]
    ) == 3


def test_demo_output_contains_top_opportunity(capsys):
    main()

    captured = capsys.readouterr()

    result = json.loads(
        captured.out.strip()
    )

    assert result["top_opportunity"] is not None
    assert result["top_opportunity"]["security_type"]
    assert result["top_opportunity"]["maturity_years"] > 0
