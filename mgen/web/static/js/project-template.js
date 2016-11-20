/*
 * Project Template UI
 */
 
$(document).ready(function() {
    
    var projectId = $('#project-id').val()
    
    /** 
     * Templates container 
     */
    
    var templatesCnt = $().itemsContainer('project-templates', {
        emptyMsg: "No templates in project."
    })
    templatesCnt.setDefaultRenderFunc(function(tmpl) {
        return $('<div class="col-xs-6 col-md-4">' +
                    '<h2><a href="/template/' + tmpl.id + '">' + 
                    tmpl.name + 
                    '</a></h2>' +
                    '<h4>' + tmpl.type + '</h4>' +
                '</div>')
    })
    templatesCnt.setSource($().dataQuery("templates").filter({project_id: projectId}))
    templatesCnt.update()
    
    /**
     * New template wizard
     */
     
    var templateWiz = $('#new-template-wizard').wizard({
        
        btnNext: 'new-template-next',
        btnPrev: 'new-template-back',
        
        validate: function(ev) {
            if (this.currentStepIdx == 0) {
                this.validateIsEmpty('input#new-template-name', ev)
                this.validateIsEmpty('input#new-template-type', ev)
                
                if ($('input#new-template-import').is(':checked')) {
                    this.validateIsEmpty('input#new-template-import-file', ev)
                }
                else {
                    this.validateIsEmpty('textarea#new-template-data', ev)
                }    
            }
            
            if (this.currentStepIdx == 1) {
                $('input.template-param-prop').each(function(i, inp) {
                    var paramId = $(inp).parents('div.template-param').attr('id')
                    if ( $(inp).val() == '' ) {
                        ev.errors.push('div#' + paramId)
                    }
                })
            }
            
        }
    }).on('switched', function(ev) {
        
        if (ev.target.atTheEnd()) {
            // is it step to render template preview
            var templateData = $('#new-template-data').val()
                
            if (templateData) {
                $('#new-template-show-preview').attr('disabled', false)
            }
            else {
                $('#new-template-show-preview').attr('disabled', true)
            }
        }
        
    }).on('finished', function(ev) {
        
        // collect parameters for this template
        var params = []
        $('div.template-param').each(function(divIdx, divCont) {
            var paramData = {
                'id': Math.random().toString(36).substring(7)
            }
            $(divCont).find('input.template-param-prop').each(function(inpIdx, inp) {
                var propName = $(inp).attr('data-param-prop'),
                    propValue = $(inp).val()
                paramData[propName] = propValue
                
            })
            params.push(paramData)
        })
        
        $.ajax('/api/templates', {
            method: 'POST',
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify({
                project_id: projectId,
                name: $('#new-template-name').val(),
                type: $('#new-template-type').val(),
                do_import: $('#new-template-import').is(':checked'),
                import_from: $('#new-template-import-file').val(),
                data: $('#new-template-data').val(),
                params: params
            }),
            error: function(xhr, type, ex) {
                $().showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                $("#new-template").modal('hide')
                
                $('#dashboard-alerts').empty()
                $('#dashboard-alerts').append(
                    $('<div class="alert alert-success fade in">' +
                        '<a href="#" class="close" data-dismiss="alert">&times;</a>' +
                        'New template <strong>' +
                        data.templates[0].name +
                        '</strong> was created successfuly.' +
                      '</div>')
                )
                
                // update views
                templatesCnt.update()
                $().dataQuery('projects').filter({project_id: projectId}).one(renderProject)
            }
        })
    })[0]
    
    $('#project-add-tmpl').on('click', function() {
        templateWiz.reset()
        $('#new-template').modal()
    })
    
    /**
     * Template parameters
     *
     */
    
    $('#new-template-add-param').on('click', function() {
        var paramId = Math.random().toString(36).substring(7)
        $("#new-template-parameters").append($('<div id="param-' + paramId + '" class="template-param input-group">' +
                                                    '<hr />' +
                                                    '<label for="param-' + paramId + '">' + 
                                                    '<span class="input-group-btn">' +
                                                        '<button class="param-remove form-control" data-param-id="param-' + paramId + '" >' +
                                                            '<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>' +
                                                        '</button>' +
                                                    '</span>' +
                                                    '</label>' +
                                                    '<div class="form-inline row">' +
                                                        '<div class="form-group col-sm-3">' + 
                                                            '<input type="text" data-param-prop="name" class="template-param-prop form-control" placeholder="my-param"/>' +
                                                            '<p class="help-block">Parameter name</p>' +
                                                        '</div>' +
                                                        '<div class="form-group col-sm-4">' + 
                                                            '<input type="text" data-param-prop="default" class="template-param-prop form-control" placeholder="default"/>' +
                                                            '<p class="help-block">Default value</p>' +
                                                        '</div>' +
                                                        '<div class="form-group col-sm-5">' + 
                                                            '<input type="text" data-param-prop="description" class="template-param-prop form-control" placeholder="..."/>' +
                                                            '<p class="help-block">Description</p>' +
                                                        '</div>' +
                                                    '</div>' +
                                               '</div>'))
        $('.param-remove').on('click', function() {
            $('#' + $(this).attr('data-param-id') ).remove()
        })
        return false
    })
    
    /**
     * Template Preview
     */
    
    $('#new-template-show-preview').on('click', function() {
        var templateData = $('#new-template-data').val(),
            templateType = $('#new-template-type').val()
            
        if (templateData) {
            $.ajax('/preview/template?type=' +  templateType, {
                method: 'POST',
                dataType: 'html',
                data: templateData,
                error: function(xhr, type, ex) {
                    $().showErrorDialog(ex, xhr.responseText)
                },
                success: function(data) {
                    var iframe = $('#new-template-preview'),
                        iframedoc = iframe[0].contentDocument || iframe[0].contentWindow.document
                    $(iframedoc.body).empty()
                    $(iframedoc.body).append($(data))
                }
            })
        }
        return false
    })
    
    /**
     * Template import
     */
    
    $('#new-template-import').on('change', function() {
        // toggle disabled attribute on inputs
        $('#new-template-import-file').prop('disabled', function(i, v) { return !v; });
        $('#new-template-data').prop('disabled', function(i, v) { return !v; });
        return false
    })
})