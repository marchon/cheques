// Copyright (c) 2016, Diamo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cheque', {
	refresh: function(frm) {
	}
});



cur_frm.fields_dict.sucursal.get_query = function(doc,cdt,cdn) {
	return{
		filters:[
			['banco', '=', doc.banco]
		]
	}
}
