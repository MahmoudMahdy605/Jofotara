import click
import frappe
from frappe.commands import pass_context

@click.command('enable-jofotara')
@click.option('--company', help='Company name to enable JoFotara for')
@pass_context
def enable_jofotara(context, company=None):
    """Enable JoFotara integration for a company"""
    from jofotara.setup.enable_integration import execute
    
    site = context.sites[0]
    frappe.init(site=site)
    frappe.connect()
    
    try:
        result = execute(company)
        
        if result["status"] == "Success":
            click.secho(result["message"], fg="green")
            click.echo("\nJoFotara integration has been enabled successfully!")
            click.echo("You can now submit Sales Invoices to generate JoFotara XML.")
        else:
            click.secho(f"Error: {result['message']}", fg="red")
            
    except Exception as e:
        click.secho(f"Error enabling JoFotara integration: {str(e)}", fg="red")
    finally:
        frappe.destroy()

commands = [
    enable_jofotara
]
