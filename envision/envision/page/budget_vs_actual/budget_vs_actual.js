frappe.pages['budget-vs-actual'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Budget Vs Actual',
		single_column: true
	});
	get_data()

	function get_data(){
		frappe.call({
			method: 'envision.envision.page.budget_vs_actual.budget_vs_actual.get_data',
			callback: function(response){
				var table_1_data = response.message[0];
				var table_2_data = response.message[1];
				// console.log("asdf0", data)
				$("#1").remove();
				$("#2").remove();
				$(frappe.render_template("budget_vs_actual_template", {table_1_data: table_1_data, table_2_data: table_2_data})).appendTo(page.body);
			}
		})
	}
}