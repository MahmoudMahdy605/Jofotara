frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if (frm.doc.docstatus !== 1) return;

        // Check if JoFotara integration is enabled for this company
        frappe.db.get_value('Company', frm.doc.company, 'enable_jofotara_integration', function(r) {
            if (!(r && r.enable_jofotara_integration)) return;

            // Button: Generate JoFotara XML
            frm.add_custom_button(__('Generate JoFotara XML'), function() {
                frappe.call({
                    method: 'jofotara.api.generate_and_view_xml',
                    args: {
                        'doctype': 'Sales Invoice',
                        'docname': frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            let d = new frappe.ui.Dialog({
                                title: __('JoFotara XML'),
                                fields: [{
                                    fieldtype: 'Code',
                                    fieldname: 'xml_content',
                                    label: __('XML Content'),
                                    options: 'XML',
                                    read_only: 1
                                }],
                                primary_action_label: __('Download'),
                                primary_action: function() {
                                    const blob = new Blob([r.message], { type: 'text/xml' });
                                    const link = document.createElement('a');
                                    link.href = window.URL.createObjectURL(blob);
                                    link.download = frm.doc.name + '_jofotara.xml';
                                    link.click();
                                    d.hide();
                                }
                            });
                            d.fields_dict.xml_content.set_value(r.message);
                            d.show();
                            frm.reload_doc();
                        }
                    }
                });
            }, __('JoFotara'));

            // Button: View XML (only if file exists)
            if (frm.doc.jofotara_xml_file) {
                frm.add_custom_button(__('View JoFotara XML'), function() {
                    window.open(frm.doc.jofotara_xml_file);
                }, __('JoFotara'));
            }

            // Button: Submit to JoFotara (only if XML was generated)
            if (frm.doc.jofotara_xml_generated) {
                frm.add_custom_button(__('Submit to JoFotara'), function() {
                    frappe.call({
                        method: 'jofotara.api.submit_to_jofotara',
                        args: {
                            docname: frm.doc.name
                        },
                        callback: function(res) {
                            if (res.message === "success") {
                                frappe.msgprint(__('✅ XML successfully submitted to JoFotara.'));
                                frm.reload_doc();
                            } else {
                                frappe.msgprint(__('❌ Failed to submit XML: ') + res.message);
                            }
                        }
                    });
                }, __('JoFotara'));
            }
        });
    }
});
