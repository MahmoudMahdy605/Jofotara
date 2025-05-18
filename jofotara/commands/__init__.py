import click
import frappe
from frappe.commands import pass_context

@click.command('setup-jofotara')
@pass_context
def setup_jofotara(context):
    """Setup JoFotara integration - creates all necessary custom fields"""
    from jofotara.setup.setup_wizard import setup_jofotara
    
    site = context.sites[0]
    frappe.init(site=site)
    frappe.connect()
    
    try:
        result = setup_jofotara()
        
        # Print summary
        click.echo(f"\n{result['summary']}")
        
        # Print detailed messages
        if result['messages']:
            click.echo("\nDetailed messages:")
            for msg in result['messages']:
                click.echo(f"- {msg}")
                
        if result['status'] == 'Success':
            click.echo("\nJoFotara integration setup completed successfully!")
            click.echo("Now you can enable JoFotara integration in your Company settings.")
        else:
            click.echo("\nJoFotara integration setup completed with issues. Please check the messages above.")
            
    except Exception as e:
        click.echo(f"Error setting up JoFotara integration: {str(e)}")
    finally:
        frappe.destroy()

commands = [
    setup_jofotara
]
