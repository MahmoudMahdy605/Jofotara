from frappe import _

def get_data():
    return [
        {
            "label": _("JoFotara E-Invoicing"),
            "icon": "fa fa-money",
            "items": [
                {
                    "type": "doctype",
                    "name": "Company",
                    "label": _("Company Settings"),
                    "description": _("Configure JoFotara integration in Company settings")
                },
                {
                    "type": "page",
                    "name": "jofotara-setup",
                    "label": _("JoFotara Setup"),
                    "description": _("Setup JoFotara integration")
                }
            ]
        },
        {
            "label": _("Help"),
            "icon": "fa fa-question-circle",
            "items": [
                {
                    "type": "doctype",
                    "name": "Sales Invoice",
                    "label": _("Sales Invoice"),
                    "description": _("Generate JoFotara XML for Sales Invoices")
                }
            ]
        }
    ]
