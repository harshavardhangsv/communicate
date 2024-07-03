$(document).ready(function(){
    a = ''
    options = [["a", "b", "c"], ["p","q","r"], ["w","x","y","z"]];
    function get_text(id) {
        var k = '<select class="something" id="something' + String(id)  + '"><br>'
        for(i=0;i<options[Number(id)].length;i++) {
            k += '<option value="' + options[Number(id)][i] + '"> ' + options[Number(id)][i] + '</option><br>'
        }
            k += '</select><br>'
            k += '<button class="change" data-wid="' +String(id) + '">Change</button>'
        return k
    }
    $('.word').each(function(){
        $(this).qtip({
            content : {
                text: get_text($(this).attr('id'))
            },
            style : {
                classes: 'qtip-bootstrap custom-qtip'
            },
            show: 'click',
            hide: 'unfocus'
        });  
    });
    $(document).on('click', '.change', function() {
        a = $('#something'+$(this).data('wid'));
        alert(a[0].value);
    }); 
});
