/**
 * Template UI
 */


$(document).ready(function() {
    
    // global list of template types
    var templateTypes = JSON.parse($('input#template-types').val()),
        templateId = $('#template-id').val(),
        allowEdit = $('#allow_edit').val() > 0,
        typesList = []

    // prepare types source list
    for(var typeId in templateTypes) {
        typesList.push({value: typeId, text: templateTypes[typeId]})
    }
    
    /**
     * Template properties modification
     * with bootstrap editable
     */
    $.fn.editable.defaults.mode = 'inline'
    $.fn.editable.defaults.ajaxOptions = {
        type: 'put',
        // keep content type as www-form-encoded here
        // but answer as json
        dataType: 'json'
    };
    
    // setup editable fields
    $('a#name').editable()
    $('a.template-param').editable()
    $('pre#data').editable()
    $('a#type').editable({ source: typesList })
    
    // parameters selector
    $('input.template-param-select').on('click', function() {
        var checked = false,
            rmParamBtn = $('button#template-remove-param')
        $('input.template-param-select').each(function(i, inp) {
            if ($(inp).is(':checked')) {
                rmParamBtn.removeClass('disabled')
                checked = true
                return false
            }
        })
        if (!checked && !rmParamBtn.hasClass('disabled'))
            rmParamBtn.addClass('disabled')
    })
    
    // add new parameter to template
    $('button#template-add-param').on('click', function() {
        
        var buildEditableSpan = function(paramId, paramValue, paramPropName, paramDesc) {
            return '<span><a href="#" ' +
                    'id="' + paramPropName + '"' +
                    'class="template-param editable editable-click"' +
                    'data-type="text" ' +
                    'data-pk="template.params.' + paramId + '" ' +
                    'data-url="/api/templates/' + templateId + '"' +
                    'data-title="' + paramDesc + '">' +
                    paramValue + '</a></span>'
                    
        }
        var selectors = $('input.template-param-select'),
            newParamData = {
            'id': Math.random().toString(36).substring(7),
            'name': 'new-' + (selectors.length + 1),
            'default': 'default',
            'description': 'Untitled parameter'
        }
        
        // create new parameter with default values
        $.ajax('/api/templates/' + templateId, {
            method: 'PUT',
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify({
                'pk': 'new.params',
                'name': 'new',
                'value': newParamData
            })
        })
        
        $('table#template-params tr:last').after($(
            '<tr>' +
                '<td style="text-align: center;" >' +
                    '<input type="checkbox" class="template-param-select" data-param-id="' + newParamData.id + '" />' +
                '</td>' +
                '<td>' +
                    ( allowEdit ? buildEditableSpan(newParamData.id, newParamData.name, 'name', 'Parameter name') : '<span>' + newParamData.name + '</span>' ) +
                '</td>' +
                '<td>' +
                    ( allowEdit ? buildEditableSpan(newParamData.id, newParamData.default, 'default', 'Default value') : '<span>' + newParamData.default + '</span>' ) +
                '</td>' +
                '<td>' +
                    ( allowEdit ? buildEditableSpan(newParamData.id, newParamData.description, 'description', 'Description') : '<span>' + newParamData.description + '</span>' ) +
                '</td>' +
            '</tr>')
        )
        
        return false
    })
})
