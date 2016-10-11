// Copyright (c) 2016, Diamo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cheque', {
	banco: function(frm) {
		// Cuando cambia el banco que saque la sucursal si tenia seleccionada.
		frm.set_value("sucursal", null);
	}
});


// Solo muestre sucursales del banco seleccionado
cur_frm.fields_dict.sucursal.get_query = function(doc,cdt,cdn) {
	return{
		filters:[
			['banco', '=', doc.banco]
		]
	}
}
