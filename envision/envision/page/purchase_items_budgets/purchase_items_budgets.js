frappe.pages['purchase-items-budgets'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Bifurcation from Material Category Expense',
		single_column: true
	});

	get_data()
	function get_data(project, from_date, to_date){

		frappe.call({
			method: 'envision.envision.page.purchase_items_budgets.purchase_items_budgets.get_data',
			// args: {
			// 	project: project,
			// 	from_date: from_date,
			// 	to_date: to_date
			// },
			callback: function(response) {
				var Data = response.message;
				$("#1").remove();
				$(frappe.render_template("purchase_items_budgets_template", {Data: Data})).appendTo(page.body);
			}
		})
	}
}