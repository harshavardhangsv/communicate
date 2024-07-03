/*jslint browser: true*/
/*global $, jQuery, alert, console*/

var ip_address = "http://10.4.16.154:9004";
var stack = Array();
var uni, dbid, ilparser_output, ime_preference;

//These variables are for bracketing, coloring of buttons
var open_bracket = true;
var color_index = 0;
var colors = ['red', 'blue', 'yellow', 'brown', 'pink', 'cyan', 'orange', 'grey', 'magenta', 'aqua', 'cadetblue'];
var open_brackets_list = Array();
var close_brackets_list = Array();
var scope_word = '';
var click_count = 0;

var prakriti_word = ''; //This variable is for inline editing of prakriti word
var proper_noun_list = Array(); //This Object is used to store all the proper nouns marked by user
var all_chunks = Array();
var chunk_list = Array();
var conjunction_words = ['और', 'कहा'];
var tokenized_text;
var chunking_output;
var compoundnouns = Object();
var complexpredicates = Object();
var mass_noun_list = Array();
var definite_noun_list = Array();

var flags = {'chnk': true, 'cst': true, 'cnt': true, 'mnt': false};   //section flags
var api_url = '';
var bar;

var shiftIsPresses = false;
var cntrlIsPressed = false;
var altIsPressed = false;


function reset() {
    stack = Array();
    open_bracket = true;
    color_index = 0;
    open_brackets_list = Array();
    close_brackets_list = Array();
    prakriti_word = '';
    scope_word = '';
    click_count = 0;
    proper_noun_list = Array();
    all_chunks = Array();
    chunk_list = Array();
    compoundnouns = Object();
    complexpredicates = Object();
    flags = {'chnk': true, 'cst': true, 'cnt': true, 'mnt': false};
    $("#translated_output").html("");
    shiftIsPresses = false;
    cntrlIsPressed = false;
    altIsPressed = false;
}


function reset_brackets() {
    open_bracket = true;
    color_index = 0;
    open_brackets_list = Array();
    close_brackets_list = Array();
    scope_word = '';
    click_count = 0;
}


function complex_sentence_intelligence () {
    if (document.getElementById('complex_sentence_tagging_checkbox').checked) {
        var words = $("#hin_input").val().split(" ");
        var index = 0;
        for(index = 0;index < conjunction_words.length; index += 1) {
            if (words.indexOf(conjunction_words[index]) != -1) {
                break;
            }
        }
        if(index == conjunction_words.length) {
            swal({
                    title: "Are you sure?",
                    text: "I can't detect a complex sentence",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#DD6B55",
                    confirmButtonText: "Yes",
                    cancelButtonText: "No, Deselect it",
                    closeOnConfirm: false,
                    closeOnCancel: false
            },
            function (isConfirm) {
                if(isConfirm) {
                    swal("OK", "Thanks for the feedback", "success"); 
                } else {
                    $('.switchery')[0].click();
                    swal("Turn Off", "Deselected", "success"); 
                }
            });
        }
    }
}


function initialize() {
    "use strict";
    $('html, body').animate({
        scrollTop: 0
    }, 100);
    var elem = $('.js-switch');
    var index;
    for(index = 0; index < elem.length; index+=1) {
        var init = new Switchery(elem[index], {'size':'small'});        
    }
    $('#complexhelp[title]').qtip({
        style : {
            classes: 'qtip-bootstrap'
        }
    });
    //this is to intialize the values in the inputmethod
    $("#hin_input").ime({
        languages : ['hi', 'en']
    });
    ime_preference = $.ime;
    $.ime.preferences.setLanguage('hi');
    $.ime.preferences.setIM($.ime.languages.hi.inputmethods[5]);
    $('.sidebar-nav').on('click', 'a', function (e){
        e.preventDefault();
        $('html, body').animate({ 
            scrollTop: $($(this).attr("href")).offset().top
        }, 'slow');
        return false;
    });

    //bar
    bar = new ProgressBar.Circle("#loading_image", {
      color: '#aaa',
      // This has to be the same size as the maximum width to
      // prevent clipping
      strokeWidth: 4,
      trailWidth: 1,
      easing: 'easeInOut',
      text: {
        autoStyleContainer: false
      },
      from: { color: '#aaa', width: 1 },
      to: { color: '#333', width: 4 },
      // Set default step function for all animate calls
      step: function(state, circle) {
        circle.path.setAttribute('stroke', state.color);
        circle.path.setAttribute('stroke-width', state.width);

        var value = Math.round(circle.value() * 100);
        if (value === 0) {
          circle.setText('');
        } else {
          circle.setText(value);
        }
      }
    });
    bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
    bar.text.style.fontSize = '2rem';


    $(document).on("click", ".flip-button", function () {
        document.querySelector("#myCard").classList.toggle("flip");
    });


    $(".ToolPage").bind('mousewheel', function(e, d)  {
        var t = $(this);
        if (d > 0 && t.scrollTop() === 0) {
            e.preventDefault();
        }
        else {
            if (d < 0 && (t.scrollTop() == t.get(0).scrollHeight - t.innerHeight())) {
                e.preventDefault();
            }
        }
    });
}

function createButtons(temp_output, set_parser_output) {
    "use strict";
    //This is to create buttons with options so that user can correct chl form
    var html = '', index, result, sentence_index, output;
    dbid = Number(temp_output[0]);
    output = temp_output[1];
    console.log(temp_output);
    uni = output;

    //enter ilparser output into the modal
    if (set_parser_output) {
        ilparser_output = temp_output[2];
        $("#parsed_sent")[0].innerHTML = ilparser_output.split("\n").join("<br>");
    }
    
    //create buttons
    for (sentence_index = 0; sentence_index < output.length; sentence_index += 1) {
        result = output[sentence_index].chl_result;
        var words = output[sentence_index].words;
        //console.log(result);
        for (index in result) {
            if (result[index].brackets.open) {
                for (var i=0;i<result[index].brackets.open;i+=1) {
                    html += '[ '
                }
            }
            var prakriti_value = result[index].prakriti;
            if (words[index].propernoun) { prakriti_value += '_named';}    
            var place_rhead =  sentence_index.toString() + '_' + index.toString();
            if (result[index].prakriti_attached.length > 1) {
                if (words[index].finer_tag == 'n') {
                    var tooltip_html = 'data-toggle="tooltip" data-placement="top" title="' + words[index].fs_list + '" ';
                }
                else {
                    var tooltip_html = 'data-toggle="tooltip" data-placement="top" title=""';
                }
                html += '<button class="word prakriti-word btn btn-link"' + tooltip_html + 'id="' + place_rhead + '" data-wid="' + index.toString() + '" data-sid="' + sentence_index.toString() + '" data-type="prakriti" >' + prakriti_value + '</button>';
            } else {
                if (words[index].finer_tag == 'n') {
                    html += '<span contenteditable=true class="prakriti-word" id="' + place_rhead + '" data-wid="' + index.toString() + '" data-sid="' + sentence_index.toString() + '" data-toggle="tooltip" data-placement="top" title="' + words[index].fs_list + '" >' + prakriti_value + '</span>';
                } else {
                    html += '<span contenteditable=true class="prakriti-word" id="' + place_rhead + '" data-wid="' + index.toString() + '" data-sid="' + sentence_index.toString() + '" data-toggle="tooltip" data-placement="top" title="" >' + prakriti_value + '</span>';
                }
            }
            html += '<button class="word btn btn-link pratyaya-word" data-rheadid="' + sentence_index.toString() + '_' + words[index]['rhead'] + '" id="' + index.toString() + '" data-wid="' + index.toString() + '" data-sid="' + sentence_index.toString() + '" data-type="pratyaya" >' + result[index].pratyaya + '</button>';
            /*if (Number(words[index]['rhead'])) {
                html += "<span class=\"rhead-show\" data-rheadid=" + words[index]['rhead'] + ">: " + (Number(words[index]['rhead']) + 1)  + "</span>   ";
            } else {*/
            html += '<span class="rhead-show"></span>';
            //}
            if (result[index].brackets.close) {
                for(var i=0;i<result[index].brackets.close;i+=1) {
                    html += '] '
                }
            }
        }
        html += '<br>';
    }
    //console.log(html);
    $('#output').html(html);
    $("#loading_image").hide();
    $("#answer_row").show();
}


function presteps() {
    var flag_complex_sentence_tagging = document.getElementById("complex_sentence_tagging_checkbox").checked;
    var flag_compound_noun_tagging = document.getElementById("proper_noun_tagging_checkbox").checked;
    if (flag_complex_sentence_tagging) {
        $('html, body').animate({
            scrollTop: $("#input_section").offset().top
        }, 1000);
        $("#section1").show();
        complex_sentence_tagging();
    }
    if (flag_compound_noun_tagging) {
        console.log("as");    
    }
}

$(document).on('mouseover', '.pratyaya-word', function (){
    $(this).css("color", "red");
    $($('#' + $(this).data('rheadid'))[0]).css('color', 'red');
});

$(document).on('mouseout', '.pratyaya-word', function (){
    $(this).css("color", "#337ab7");
    $($('#' + $(this).data('rheadid'))[0]).css('color', 'black');
});




$(document).on('click', '.word', function (event){
    //this is the pop-up where we show options for clicked word
    $(this).qtip({
        overwrite: false,
        content : {
//                text: get_content($(this).attr('id'), $(this).data('sid'))
            text : function(event, api) {
                var wid = $(this).data('wid');
                var sid = $(this).data('sid');
                try {
                    $('#something' + wid + sid)[0].remove();
                } catch (err) {
                    console.log('not rendered yet!!')
                }
                var options_type = $(this).data('type') + '_options';
                var options = uni[sid]['chl_result'][wid][options_type];
                var html = '<fieldset class="form-group"><br>';
                html += '<label for="something' + wid + sid + '">Select a relation</label><br>';
                //html += '<select class="form-control customselect selectpicker" data-live-search="true" id="something' + wid + sid + '" data-sid="' + sid + '" data-wid="' + wid + '" data-type="' + $(this).data('type') + '"><br>';
                html += '<select class="selectpicker show-tick form-control" data-live-search="true" id="something' + wid + sid + '" data-sid="' + sid + '" data-wid="' + wid + '" data-type="' + $(this).data('type') + '"><br>';
                html += '<option name="select">Select a relation</option><br>';    
                for(var drel in options) {
                    //console.log(options);
                    var relation_name = options[drel].name;
                    html += '<option name="' + drel + '">' + relation_name + '</option><br>';
                }
                html += '</select><br>';
                html += '<label for="rhead' + wid + sid + '">Select Indices</label><br>';
                html += '<select class="selectpicker show-tick form-control rhead-selection" data-live-search="true" id="rhead' + wid + sid + '" data-sid="' + sid + '" data-wid="' + wid + '" data-type="' + $(this).data('type') + '"><br>';
                var flag = 0;
                for(var i in uni[sid]['chl_result']) {
                    if ( Number(wid) < Number(i) && uni[sid]['words'][Number(i)]['pos_tag'] == 'VM' && flag == 0) {
                        html += '<option name="' + i + '" selected>' + (Number(i)+1) + ':' + uni[sid]['chl_result'][i]['prakriti'] + '</option><br>';
                        flag = 1;
                    } else {
                        html += '<option name="' + i + '">' + (Number(i)+1) + ':' + uni[sid]['chl_result'][i]['prakriti'] + '</option><br>';
                    }
                }
                html += '<option name="-1">0:root</option><br>';
                html += '</select><br>';
                html += '<button class="btn btn-xs btn-primary custombutton" data-sid="' + sid + '" data-wid="' + wid + '" id="button' + wid + sid +'" data-selectid="something' + wid + sid + '">Submit</button><br>';
                html += '</fieldset>';
                return html;
            }
        },
        show : {
            event: event.type,
            ready: true
        },
        position: {
            my: 'top center',  // Position my top left...
            at: 'bottom center' // at the bottom right of...
        },
        hide : 'unfocus',
        style : {
            classes: 'qtip-bootstrap customclass'
        },
        events: {
            visible: function (et, api) {
                $('select').select2();
            }
        }
    }, event);
});


$(document).on('click', '.custombutton', function (){
    //This is button which is clicked to enable the change of relation on a chl word
    var selectid = $(this).data('selectid');
    var wid = $('#'+selectid).data('wid');
    var sid = $('#'+selectid).data('sid');
    var select_element = $('#'+selectid)[0];
    var type = $('#'+selectid).data('type');
    var prev_drel = uni[sid]['words'][wid].drel;
    var next_drel;
    if(type == 'pratyaya') {
        //console.log('#rhead' + wid + sid);
        var new_rhead = Number($('#rhead'+wid+sid).find('option:selected').attr('name'));
        console.log(new_rhead);
        if($(select_element).find('option:selected').attr('name') == 'lwg__psp') { //this is to create the rhead for raw_annotation of a sentence
            uni[sid]['words'][wid].rhead = new_rhead;
        }
        if($(select_element).find('option:selected').attr('name') == 'lwg__vaux') { //this is to create the rhead for raw_annotation of a sentence
            uni[sid]['words'][wid].rhead = new_rhead;                
        }
        //console.log(uni);
        uni[sid]['words'][wid].rhead = new_rhead;
        //console.log(uni);
        if(uni[sid]['chl_result'][wid].conjunction_index != -1) {
            var conjunction_index = uni[sid]['chl_result'][wid].conjunction_index;
            prev_drel = uni[sid]['words'][conjunction_index].drel;
            if ($(select_element).find('option:selected').attr('name') != "select") {
                uni[sid]['words'][conjunction_index].drel = $(select_element).find('option:selected').attr('name');
                next_drel = uni[sid]['words'][conjunction_index].drel;  
            }
        } else {
            if ($(select_element).find('option:selected').attr('name') != "select") {
                uni[sid]['words'][wid].drel = $(select_element).find('option:selected').attr('name');
                next_drel = uni[sid]['words'][wid].drel;
            }
        }
        stack.push({sid: sid, wid: wid, prev_drel: prev_drel, next_drel: next_drel});                
    } else {
        var selected_value = $(select_element).find('option:selected').attr('name');
        var split_integer = Number(selected_value.replace('split', ''));
        var attached_ids = uni[sid]['chl_result'][wid].prakriti_attached;
        console.log(uni);
        if(split_integer == 0) { 
            split_integer = attached_ids.length - 1;
            for(var i=0;i<split_integer;i+=1) {
                prev_drel = uni[sid]['words'][attached_ids[i]].drel;
                uni[sid]['words'][attached_ids[i]].drel = '-';
                next_drel = uni[sid]['words'][attached_ids[i]].drel;
                stack.push({sid: sid, wid: attached_ids[i], prev_drel: prev_drel, next_drel: '-'});
            }
        } else {
            prev_drel = uni[sid]['words'][attached_ids[split_integer-1]].drel;
            uni[sid]['words'][attached_ids[split_integer-1]].drel = '-';
            next_drel = uni[sid]['words'][attached_ids[split_integer-1]].drel;
            stack.push({sid: sid, wid: attached_ids[split_integer-1], prev_drel: prev_drel, next_drel: '-'});
        }
    }
    //console.log($(select_element).find('option:selected').attr('name'));
    //console.log(uni[sid]['words'][wid].drel);
    //console.log(uni);
    $.ajax({
        url: ip_address + "/change",
        method: "POST",
        data: {
                "dbid": dbid,
                "result": JSON.stringify(uni),
                "new_relation_weight": JSON.stringify({"prev_drel": prev_drel, "next_drel": next_drel, "pratyaya_value": uni[sid]["chl_result"][wid].pratyaya_value})
        },
        //contentType: "application/json; charset=utf-8",
        dataType: "JSON",
        success: function(output) {
            //console.log(output);
            createButtons(output, 0);
            $('#'+$("#"+selectid).parent().parent().parent().attr("id")).detach();
        }
    });
});


$(document).on('click', '#undo', function() {
    //This action is for undo button on CHL form changing
    var element = stack.pop();
    if(element) {
        var sid = element.sid;
        var wid = element.wid;
        var prev_drel = element.prev_drel;
        var next_drel = element.next_drel;
        if (uni[sid]['words'][wid].drel == next_drel) {
            uni[sid]['words'][wid].drel = prev_drel;
            $.ajax({
                url: ip_address + "/change",
                method: "POST",
                data: {
                    "dbid": dbid,
                    "result": JSON.stringify(uni),
                    "new_relation_weight": JSON.stringify({"prev_drel": prev_drel, "next_drel": next_drel, "pratyaya_value": uni[sid]["chl_result"][wid].pratyaya_value})
                },
                //contentType: "application/json; charset=utf-8",
                dataType: "JSON",
                success: function(output) {
                    //console.log(output);
                    createButtons(output, 0);
                }
            });
        } else {
            console.log('Something wrong with stack insertion');
        }
    }
});


$(document).on("click", "#save_button", function() {
    var feedback = $("#feedback_textarea")[0].value;
    $.ajax({
        url: ip_address + "/feedback",
        type: "post",
        data: {"dbid": dbid, "feedback": feedback},
        success: function() {
            console.log('Successfully Saved in database');
            $("#hin_input")[0].value = "";
            location.reload();
            //toastr["success"]("Saved into database succesfully", "Success");
        }
    });
});


$(document).on('click', '#raw_annotate', function (){
    $.ajax({
        url: ip_address + "/raw_annotate",
        method: "POST",
        data: { "input_text": $('#hin_input').val() },
        dataType: "JSON",
        success: function (output){
            createButtons(output, 0);
        }
    });
});


$(document).on('blur', '.prakriti-word', function (){
    //console.log($(this).text());
    if (prakriti_word != $(this).text()) {
        var sid, wid;
        sid = $(this).data('sid');
        wid = $(this).data('wid');
        uni[sid]['words'][wid].word_utf8 = $(this).text();
        $.ajax({
            url: ip_address + '/save_modified_words',
            method: 'POST',
            data: { 'uni': JSON.stringify(uni), 'dbid': dbid },
            success: function (response){
                console.log(response);
            }
        });
    }
});


$(document).on('focus', '.prakriti-word', function (){
    //console.log($(this).text());
    prakriti_word = $(this).text();
});


function run_parser() {
    $("#default_chl_text").hide();
    $('#answer_row').hide();
    $("#loading_image").show();
    bar.animate(1.0, { duration: 8000 * $("#hin_input").val().split("\n").length });
    $.ajax({
        url: ip_address + api_url,
        method: 'POST',
        data:   {
            "mainInput": $("#hin_input").val(),
            "open_brackets_list": JSON.stringify(open_brackets_list),
            "close_brackets_list": JSON.stringify(close_brackets_list),
            "proper_noun_list": JSON.stringify(proper_noun_list),
            "chnk_html": $("#chnk_text").html(),
            "chunking_output": JSON.stringify(chunking_output),
            "compoundnouns": JSON.stringify(compoundnouns),
            "complexpredicates": JSON.stringify(complexpredicates)
        },
        dataType: 'JSON',
        success: function (output) {
            createButtons(output, 0);
        }
    });
    $('html, body').animate({
        scrollTop: $("#chl_section").offset().top
    }, 1000);
}


$(document).on('click', '.section-submit', function (){
    flags[$(this).data('uid')] = true;
    //console.log(flags);
    if(flags['chnk'] && flags['cst'] && flags['cnt'] && flags['mnt']) {
        run_parser();
    } else {
        $('html, body').animate({
            scrollTop: $(window).scrollTop() + $(window).height()
        }, 1000);
    }
});


$(document).on('click', '#join-chunk', function (){
    /*
        IN SECTION CHUNKING,
        We join the so far selected words and reset the CHUNK_LIST
    */
    var index, chunk_value;
    var sid, wid;
    if (chunk_list.length > 1) {
        var first_element =  chunk_list[0];
        var first_wid = first_element[1];
        var first_chunk_list = chunking_output[first_element[0]][first_wid];
        var first_chunk_last_word_index = first_chunk_list[first_chunk_list.length-1];
        sid = first_element[0];
        if ($(this).data('jointype') == 'compoundnoun') {
            if (!compoundnouns[sid]) {
                compoundnouns[sid] = Array();
            }
            compoundnouns[sid].push(first_chunk_last_word_index);
        } else if ($(this).data('jointype') == 'complexpredicate') {
            if (!complexpredicates[sid]) {
                complexpredicates[sid] = Array();
            }
            complexpredicates[sid].push(first_chunk_last_word_index);
        }
        for (index = 1; index < chunk_list.length; index += 1) {
            sid = chunk_list[index][0];
            wid = chunk_list[index][1];
            chunking_output[sid][first_wid] = chunking_output[sid][first_wid].concat(chunking_output[sid][wid]);
            delete chunking_output[sid][wid];
        }
        chunk_list = Array();
        create_chnk_section(chunking_output);
    }
});


$(document).on('click', '#split-chunk', function (){
    /*
        IN SECTION CHUNKING,
        We split the so far selected words and reset the CHUNK_LIST
    */
    var index, chunk_value;
    var sid, wid, j;
    if (chunk_list.length) {
        for (index = 0; index < chunk_list.length; index += 1) {
            sid = chunk_list[index][0];
            wid = chunk_list[index][1];
            var new_list = chunking_output[sid][wid];
            delete chunking_output[sid][wid];
            if (compoundnouns[sid]) {
                if(compoundnouns[sid].indexOf(wid) != -1) {
                    delete compoundnouns[sid][compoundnouns[sid].indexOf(wid)];
                }
            }
            if (complexpredicates[sid]) {
                if(complexpredicates[sid].indexOf(wid) != -1) {
                    delete complexpredicates[sid][complexpredicates[sid].indexOf(wid)];
                }
            }
            for(j = 0; j < new_list.length; j += 1) {
                chunking_output[sid][new_list[j]] = [new_list[j]];
            }
        }
        chunk_list = Array();
        create_chnk_section(chunking_output);
    }
});


$(document).on('click', '.chnk-word', function (){
    /*
        IN SECTION CHUNKING,
        A group of words are selected and then they will be 'joined' to form a chunk
        It is stored in the CHUNK_LIST
    */
    var sid = $(this).data('sid');
    var wid = $(this).data('wid');
    if ($(this).hasClass('active')) {
        chunk_list.pop(chunk_list.indexOf([sid, wid]));
        $(this).removeClass('active');
    } else {
        chunk_list.push([sid, wid]);
        $(this).addClass('active');
    }
});

$(document).on('change', '#complex_sentence_tagging_checkbox', complex_sentence_intelligence);


$(document).on('click', '#reset-brackets', function (){
    reset_brackets();
    $(".cst-word").css('background-color', '#4CAF50');
});


$(document).on('click', '.cst-word', function (){
    //this click is on words that are created to have a marking for word bracketing
    var sid = $(this).data('sid');
    var wid = $(this).data('wid');
//    console.log($(this).data());
    if (click_count == 0) {
        scope_word = $(this).text();
        click_count = (click_count + 1) % 3;
    }
    else if (open_bracket) {  //open bracket
        $(this).css('background-color', colors[color_index]);
        open_brackets_list.push([scope_word, sid, wid]);
        open_bracket = false;
        click_count = (click_count + 1) % 3;
    } else {            //close bracket
        $(this).css('background-color', colors[color_index]);
        close_brackets_list.push([scope_word, sid, wid]);
        color_index += 1;
        open_bracket = true;
        click_count = (click_count + 1) % 3;
    }
});


$(document).on('click', '.cnt-word', function (){
    /*
        IN SECTION COMMON NOUN TAGGING,
        Once a word is pressed, it will be added to the proper noun list
        If pressed twice, it will be removed from the list
    */
    var sid = $(this).data('sid');
    var wid = $(this).data('wid');
    if ($(this).hasClass('active')) {
        proper_noun_list.pop(proper_noun_list.indexOf([sid, wid]));
        $(this).removeClass('active');
    } else {
        proper_noun_list.push([sid, wid]);
        $(this).addClass('active');
    }
});


function create_chnk_section(output) {
    //console.log(output);
    var html = $(document.createElement('div'));
    var key, word_index, temp_words_list, temp_index_list, i, join_parameter, html_text;
    for (sentence_id = 0;sentence_id < output.length; sentence_id += 1) {
        for (key in output[sentence_id]) {
            //console.log(output[sentence_id]);
            temp_html = $(document.createElement('a'));
            temp_words_list = Array();
            temp_index_list = Array();
            for (word_index = 0; word_index < output[sentence_id][key].length; word_index += 1) {
                temp_words_list.push(tokenized_text[sentence_id][output[sentence_id][key][word_index]]);
                temp_index_list.push(output[sentence_id][key][word_index]);
            }
            html_text = "";
            if (temp_index_list.length > 1) {
                for (i = 0; i < temp_index_list.length; i += 1) {
                    html_text += temp_words_list[i];
                    join_parameter = '_';
                    if (compoundnouns[sentence_id] && compoundnouns[sentence_id].indexOf(temp_index_list[i]) != -1) {
                        join_parameter = '+';
                    }
                    if (complexpredicates[sentence_id] && complexpredicates[sentence_id].indexOf(temp_index_list[i]) != -1) {
                        join_parameter = '+';
                    }
                    if (i + 1 != temp_index_list.length) {
                        html_text += join_parameter;
                    }
                }
            } else {
                html_text = temp_words_list.join('_');
            }
            temp_html.text(html_text);
            temp_html.addClass('chnk-word');
            temp_html.addClass('btn');
            temp_html.addClass('btn-default');
            temp_html.attr('id', 'chnk'+sentence_id+key);
            temp_html.attr('data-sid', sentence_id);
            temp_html.attr('data-wid', key);
            html.append(temp_html);
        }
        html.append('<br>');
    }
    //console.log(html);
    $('#chnk_text').html('');
    $(html).appendTo('#chnk_text');
}


function create_sections(checkboxes) {
    var sentence_id, word_id, temp_html;
    for(task in checkboxes) {
        if (checkboxes[task]) {
            var html = $(document.createElement('div'));
            for (sentence_id = 0;sentence_id < tokenized_text.length; sentence_id += 1) {
                for (word_id = 0;word_id < tokenized_text[sentence_id].length; word_id += 1) {
                    temp_html = $(document.createElement('a'));
                    temp_html.text(tokenized_text[sentence_id][word_id]);
                    temp_html.addClass(task + '-word');
                    temp_html.addClass('btn');
                    temp_html.addClass('btn-default');
                    temp_html.attr('id', task+sentence_id+word_id);
                    temp_html.attr('data-sid', sentence_id);
                    temp_html.attr('data-wid', word_id);
                    html.append(temp_html);
                }
                html.append('<br>');
            }
            //console.log(html);
            $("#" + task + '_text').html('');
            $(html).appendTo('#' + task + '_text');
        }
    }
    create_mnt_section();
    if (checkboxes['chnk']) {
        $.ajax({
            url: ip_address + '/get_chunking',
            method: 'POST',
            data: { 'hin_input': $('#hin_input').val(), 'tokenized_text': JSON.stringify(tokenized_text) },
            dataType: 'JSON',
            success: function (output){
                //console.log(output);
                chunking_output = output;
                create_chnk_section(output);
            }
        });
    }
    $('html, body').animate({
        scrollTop: $(window).scrollTop() + $(window).height()
    }, 1000);
}


function tokenize(hin_text, cst_checkbox, cnt_checkbox, chnk_checkbox, mnt_checkbox) {
    $.ajax({
        url: ip_address + '/tokenize',
        type: 'post',
        data: {'hin_text': hin_text},
        dataType: 'JSON',
        success: function (output){
                    tokenized_text = output['tokenized_output'];
                    create_sections({ 'cst': cst_checkbox, 'cnt': cnt_checkbox, 'chnk': chnk_checkbox});
                }
    });
}


$(document).ready(function () {
    initialize();
    $("#all_buttons a").click(function (){
        api_url = '/' + $(this).data('api');
        if ($("#hin_input").val()) {
            //NAVBAR,SECTIONS START
            reset();
            $('#sidebar-wrapper').show();
            $('#sidebar-wrapper').find('*').show();
            $('.section').show();
            var parser_type = $(this).attr('id');
            flags['cst']= !document.getElementById('complex_sentence_tagging_checkbox').checked;
            flags['cnt'] = !document.getElementById('proper_noun_tagging_checkbox').checked;
            var cst_checkbox = document.getElementById('complex_sentence_tagging_checkbox').checked;
            var cnt_checkbox = document.getElementById('proper_noun_tagging_checkbox').checked;
            var chnk_checkbox = true;
            var mnt_checkbox = true;
            if (parser_type != 'rule_based_convert') {
                $('#chunking_section').hide();
                $('#chunking_link').hide();
                chnk_checkbox = false;
            } else {
                flags['chnk'] = false;
            }
            if (!cst_checkbox) {
                $('#complex_sentence_section').hide();
                $('#complex_sentence_link').hide();    
            }
            if (!cnt_checkbox) {
                $('#proper_noun_section').hide();
                $('#proper_noun_link').hide();
            }
            //NAVBAR,SECTIONS END
            //console.log(flags);
            if(cst_checkbox || cnt_checkbox || chnk_checkbox || mnt_checkbox) {
                tokenize($("#hin_input").val(), cst_checkbox, cnt_checkbox, chnk_checkbox, mnt_checkbox);
            } else {
                $("#default_chl_text").hide();
                $('#answer_row').hide();
                $("#loading_image").show();
                bar.animate(1.0, { duration: 8000 * $("#hin_input").val().split("\n").length });
                $.ajax({
                    url: ip_address + api_url,
                    method: 'POST',
                    data:   {
                                "mainInput": $("#hin_input").val(),
                                "open_brackets_list": JSON.stringify(open_brackets_list),
                                "close_brackets_list": JSON.stringify(close_brackets_list),
                                "proper_noun_list": JSON.stringify(proper_noun_list)
                            },
                    dataType: 'JSON',
                    success: function(output) {
                        createButtons(output, 0);
                    }
                });
                $('html, body').animate({                    
                    scrollTop: $(window).scrollTop() + $(window).height()
                }, 1000);
            }

        }
        return false;
    });

       
    $("#translate").click(function (){
        //'This will send the CHL Text to prateek server and display the translated output'
        //var prateek_ipaddress = "http://10.2.131.136:9000";
        var output_html = $("#output").html();
        var each_chl_sentences_html = output_html.split("<br>");
        var all_sentences = Array();
        for(var i=0;i<each_chl_sentences_html.length;i+=1) {
            sent_html = each_chl_sentences_html[i];
            sent_elements = $('<div/>').html(sent_html).contents();
            sent_text = ""
            for(var j=0;j<sent_elements.length;j+=1) {
                sent_text += sent_elements[j].textContent + " ";
            }
            all_sentences.push(sent_text);
        }
        //console.log(all_sentences);
        console.log("Hello");
        console.log(uni);
        $.ajax({
            url: ip_address + "/translate",
            method: "POST",
            data: {"chl_sentences": JSON.stringify(all_sentences), "chl":JSON.stringify(uni)},
            dataType: "JSON",
            success: function (translated_sentences) {
                html = "";
                //console.log(translated_sentences);
                for(var i=0;i<translated_sentences.length;i+=1) {
                    var each_trans_sent = translated_sentences[i];
                    html += "<p><br>";
                    for(var j=0;j<each_trans_sent.length;j+=1) {
                        html += each_trans_sent[j];
                        html += "<br>";
                    }
                    html += "</p><br>";
                    //console.log(html);
                }
                $("#translated_output").html(html);
            }
        });
    });

});

/*
$(document).on('keydown', 'body', function (event){
    if (event.keyCode == 40) {
        $('html, body').animate({
            scrollTop: $(window).scrollTop() + $(window).height()
        }, 500);
    }
    else if (event.keyCode == 38) {
        $('html, body').animate({
            scrollTop: $(window).scrollTop() - $(window).height()
        }, 500);
    }
});

$(document).on('keydown', '#hin_input', function (event){
    event.stopPropagation();
});

$(document).on('keydown', '#feedback_textarea', function (event){
    event.stopPropagation();
});

*/

function sentence_intelligence () {
    if (document.getElementById('complex_sentence_tagging_checkbox').checked) {
        var words = $("#hin_input").val().split(" ");
        var index = 0;
        for(index = 0;index < conjunction_words.length; index += 1) {
            if (words.indexOf(conjunction_words[index]) != -1) {
                break;
            }
        }
        if(index == conjunction_words.length) {
            swal({
                    title: "Are you sure?",
                    text: "I can't detect a complex sentence",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#DD6B55",
                    confirmButtonText: "Yes",
                    cancelButtonText: "No, Deselect it",
                    closeOnConfirm: false,
                    closeOnCancel: false
            },
            function (isConfirm) {
                if(isConfirm) {
                    swal("OK", "Thanks for the feedback", "success"); 
                } else {
                    $('.switchery')[0].click();
                    swal("Turn Off", "Deselected", "success"); 
                }
            });
        }
    }
}

function as() {
    console.log("asdasdasd");
}

$(document).on("click", "#chl_submit", function() {

    var i, j, k;
    $('html, body').animate({
        scrollTop: $(window).scrollTop() + $(window).height()
    }, 1000);
    $.ajax({
        url: ip_address + '/get_gloss',
        method: 'post',
        data: {'uni': JSON.stringify(uni), 'dbid': dbid},
        datatype: "json",
        success: function (result) {
            uni = JSON.parse(result);
            var gloss_html = "";
            console.log(uni);
            for (i=0;i<uni.length;i+=1) {
                gloss_html += "Sentence no: " + (i+1) + " <br>";
                var es = uni[i];
                for (k in es['chl_result']) {
                    if (es['chl_result'][k]['propernoun'] == false && Object.keys(es['chl_result'][k]['gloss']).length > 0) {
                        var word = es['words'][parseInt(k)];
                        gloss_html += word['root_utf8'] + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
                        gloss_html += "<select class=\"gloss-select\" id=\"gloss_select_id" + i + '_' + k + "\" data-sid=" + i + " data-wid=" + k + ">";
                        for (j in es['chl_result'][k]['gloss']) {
                            gloss_html += "<option value=\"" + j + "\">"+ es['chl_result'][k]['gloss'][j][1]  + "</option>";
                        }
                        gloss_html += "</select><br>";
                    }
                }
            }
            $("#gloss_text").html(gloss_html);
        }
    });
});

$(document).on("click", "#gloss-submit", function (){
    var all_gloss_selects = $(".gloss-select");
    var i, sid, wid, value;
    for (i=0;i<all_gloss_selects.length;i+=1) {
        sid = $(all_gloss_selects[i]).data("sid");
        wid = $(all_gloss_selects[i]).data("wid");
        value = $(all_gloss_selects[i]).val();
        uni[sid]["chl_result"][wid]["gloss_result"] = uni[sid]["chl_result"][wid]["gloss"][value];
    }
    console.log(uni);
});

function create_mnt_section () {
    var sid, wid, k, mnt_html = "";
    var loc_tt = tokenized_text;
    $.ajax({
        url: ip_address + '/get_nouns',
        method: 'post',
        data: {'hin_input': $('#hin_input').val()},
        dataType: "JSON",
        success: function (nouns) {
            console.log(nouns);
            mnt_html += "<table border=0 class=\"table table-striped table-fixed\" cellpadding=\"10\" style=\"width:60%; margin-top:5%; text-align:center\" align=\"center\">";
            mnt_html += "<thead><tr><th style=\"text-align:center\">word</th><th style=\"text-align:center\">mass noun</th><th style=\"text-align:center\">definite noun</th></tr></thead><tbody>";
            for(sid=0;sid<loc_tt.length;sid+=1) {
                mass_noun_list[sid] = {};
                definite_noun_list[sid] = {};
                for(wid=0;wid<loc_tt[sid].length;wid+=1) {
                    mass_noun_list[sid][wid] = false;
                    definite_noun_list[sid][wid] = false;
                    if(nouns[sid.toString()][wid.toString()] == true) {
                        mnt_html += "<tr>";
                        mnt_html += "<td>" + loc_tt[sid][wid] + "</td>";
                        mnt_html += "<td align=\"center\">" + "<input type=\"checkbox\" class=\"mdnoun js-switch\" data-sid=\"" + sid  + "\" data-wid=\"" + wid  + "\" data-nountype=\"mass\" >" + "</td>";
                        mnt_html += "<td align=\"center\">" + "<input type=\"checkbox\" class=\"mdnoun js-switch\" data-sid=\"" + sid  + "\" data-wid=\"" + wid  + "\" data-nountype=\"definite\" >" + "</td>";
                        mnt_html += "</tr>";
                    }
                }
                mnt_html += "<tr></tr>";
            }    
            mnt_html += "</tbody></table>";
            $("#mass_definite_text").html(mnt_html);
            
            var elem = $('.mdnoun');
            var index;
            for(index = 0; index < elem.length; index+=1) {
                var init = new Switchery(elem[index], {'size':'small'});        
            }
        }
    });
}


$(document).on("change", ".mdnoun", function (){
    var sid, wid, nountype;
    sid = $(this).data("sid");
    wid = $(this).data("wid");
    nountype = $(this).data("nountype");
    if (nountype == "mass") {
        if(this.checked) {
            mass_noun_list[sid][wid] = true;
        } else {
            mass_noun_list[sid][wid] = false;
        }
    }
    if (nountype == "definite") {
        if(this.checked) {
            definite_noun_list[sid][wid] = true;
        } else {
            definite_noun_list[sid][wid] = false;
        }
    }
});


$(document).on("click", "#gloss-submit", function (){
    $('html, body').animate({
        scrollTop: $(window).scrollTop() + $(window).height()
    }, 1000);
    $.ajax({
        url: ip_address + '/get_csv',
        method: 'post',
        data: {'uni': JSON.stringify(uni), 'mass': JSON.stringify(mass_noun_list), 'definite': JSON.stringify(definite_noun_list), 'chunking_output': JSON.stringify(chunking_output)},
        datatype: "json",
        success: function (result) {
            console.log(result);
            json_result = JSON.parse(result);
            console.log(json_result);
            var sent, line, word, csv_html = "";
            var eng_html = "";
            for (sent=0;sent<json_result.length;sent++) {
                csv_html += "<div class=\"csv_sent\">\n";
                for (line=0;line<json_result[sent][0].length;line++) {
                    csv_html += "<div class=\"csv_line\">\n";
                    for (word=0;word<json_result[sent][0][line].length;word++) {
                        csv_html += "<input type=\"text\" class=\"csv_input\" value=\"" + json_result[sent][0][line][word] + "\">&nbsp;";
                    }
                    csv_html += "</div><br>";
                }
                csv_html += "</div><br><br>";
                eng_html += "<div class=\"eng_sent\">\n";
                for (line = 0; line < json_result[sent][1].length; line++) {
                    eng_html += "<p>" + json_result[sent][1][line] + "</p>\n";
                }
                eng_html += "</div>";
            }
            $("#csv_text").html(csv_html);
            $("#translation_output").html(eng_html);
        }
    });
});

$(document).keydown(function(event){
    if(event.which=="16")
        shiftIsPresses = true;
    if(event.which=="17")
        cntrlIsPressed = true;
    if(event.which=="18")
        altIsPressed = true;
});

$(document).keyup(function(){
    shiftIsPresses = false;
    cntrlIsPressed = false;
    altIsPressed = false;
});

