$(document).ready(function(){
	$("#up_button").click(function(){
		var item_value = $('input[name=item_radios]:checked').val();
		if (!item_value){
			alert('no select')
			return;
		}
		id = "#radio_div_" + item_value;
		item = $(id);
		item.prev(".radio").before(item);
	});
	$("#down_button").click(function(){
		var item_value = $('input[name=item_radios]:checked').val();
		if (!item_value){
			alert('no select')
			return;
		}
		id = "#radio_div_" + item_value;
		item = $(id);
		item.next(".radio").after(item)
	});
	$("#save_button").click(function(){
		items = '';
		$(".radio").each(function(){
			items += $(this).text()
		});
		$.post(window.location.href, {'data': items});
	});
	$("#sortable_div").sortable();
	$("#create_button").click(function(){
		//alert('hello');
		window.location.href = "http://www.163.com";
		//window.location.href="/create/item"
	});
});
