def validate_chart_config(chart, result):
    if not chart:
        return None

    if not result:
        return None

    if chart.get("type")==None:
        return None

    x_field=chart.get("x_field")
    y_field=chart.get("y_field")

    if not x_field or not y_field:
        return None

    columns=set(result[0].keys())

    if x_field not in columns:
        return None
    if y_field not in columns:
        return None

    try:
        for row in result:
            float(row[y_field])
    except(TypeError, ValueError, KeyError):
        return None

    return chart