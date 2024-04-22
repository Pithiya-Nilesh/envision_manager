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
				var data = response.message;
				// console.log("asdf0", data)
				$("#1").remove();
				$(frappe.render_template("budget_vs_actual_template", {data: data})).appendTo(page.body);
			}
		})
	}
}