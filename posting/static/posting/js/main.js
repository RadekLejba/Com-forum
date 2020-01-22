$(document).ready(function(){
    const $favoriteContainer = $('.favorite-container');
    $favoriteContainer.on('click', function () {
        const $link = $(this).find('.favorite'),
              object_id = $(this).attr('data-thread_id'),
              remove_url = $(this).attr('data-remove-url'),
              add_url = $(this).attr('data-add-url'),
              method = $link.attr("data-method"),
              $token_input = $(this).find("[name='csrfmiddlewaretoken']"),
              csrf_token = $token_input.attr("value");
        const url = (method === "add") ? add_url : remove_url;

        $.ajax({
            method: "POST",
            url: url,
            data: {
                'csrfmiddlewaretoken': csrf_token,
                'id': object_id,
            },
            dataType : 'json',
            success: test,
        });

        function test(data) {
          if (method === "add") {
              $link.attr("data-method", "remove");
              $link.html("<i class=\"fas fa-eye-slash\"></i>");
          } else {
              $link.attr("data-method", "add");
              $link.html("<i class=\"fas fa-eye\"></i>");
          };
        };
    });
});
