

		var csrftoken;

		function csrfSafeMethod(method) {
	    	// these HTTP methods do not require CSRF protection
	    	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
		}

		$(document).ready(function(){
			csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
			}
		);
		
		$(document).ready(function(){
			$.ajaxSetup({
		    	beforeSend: function(xhr, settings) {
		        	if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
		            	xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        	}
		    	}
			});
		});
		