/* MGEN: Static Website Generator
 * Dashboard UI magic
 */


var renderProject = function(proj) {
    $("#project-id").val(proj.project_id)
    $("#project-title").html(proj.title)
    $("#project-public-base-uri").html(proj.public_base_uri)
    
    $("#project-deploy").html('Deploy (' + proj.slugs.length + ' slugs)')
    if (proj.slugs.length <= 0)
        $("#project-deploy").addClass('disabled')
    $("#project-items-link").html(proj.items.length + ' items')
    $("#project-templates-link").html(proj.templates.length + ' templates')
}

$(document).ready(function() {
    
    /* Project details */
    
    var projectId = $('#project-id').val()
    $().dataQuery('projects').filter({project_id: projectId}).one(renderProject)
    
    /* Templates container */
    
    var templatesCnt = $().itemsContainer('project-templates', {
        emptyMsg: "No templates in project."
    })
    templatesCnt.setDefaultRenderFunc(function(item) {
        return $('<div class="col-xs-6 col-md-4">' +
            '<h2>' + item.name + '</h2>' +
            '<h4>' + item.type + '</h4>' +
        '</div>')
    })
    templatesCnt.setSource($().dataQuery("templates").filter({project_id: projectId}))
    templatesCnt.update()
    
    /* Items container */
    
    var itemsCnt = $().itemsContainer('project-items', {
        emptyMsg: "No items in project."
    })
    itemsCnt.setDefaultRenderFunc(function(tmpl) {
        return $('<div class="col-xs-6 col-md-4">' +
            '<h2>' + tmpl.name + '</h2>' +
            '<h4>' + tmpl.type + '</h4>' +
        '</div>')
    })
    itemsCnt.setSource($().dataQuery("items").filter({project_id: projectId}))
    itemsCnt.update()
    
    /* Pages container */
    
    var pagesCnt = $().itemsContainer('project-pages', {
        emptyMsg: "No pages in project."
    })
    pagesCnt.setDefaultRenderFunc(function(page) {
        return $('<div class="col-xs-6 col-md-4">' +
            '<h2>' + page.path + '</h2>' +
            '<h4>' + templatesCnt.find({template_id: page.template_id}).name + '</h4>' +
        '</div>')
    })
    pagesCnt.setSource($().dataQuery("pages").filter({project_id: projectId}))
    pagesCnt.update()
    
    /* New Item Wizard */
    
    var itemWiz = $('#new-item-wizard').wizard({
        btnNext: 'new-item-next',
        btnPrev: 'new-item-back'
    }).on('finished', function() {
        var tags = $('#new-item-tags').val()
        $.ajax('/items', {
            method: "POST",
            dataType: "json",
            data: JSON.stringify({
                project_id: projectId,
                name: $('#new-item-name').val(),
                uri_path: $('#new-item-uri').val(),
                type: $('#new-item-type').val(),
                tags: tags.length > 0 ? tags.split(',') : [],
                published: $('#new-item-published').is(':checked'),
                publish_on: $('#new-item-publish-date').val(),
                body: $('#new-item-body').val()
            }),
            error: function(xhr, type, ex) {
                $.showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                ("#new-item-create").modal('hide')
                $('#dashboard-alerts').empty()
                $('#dashboard-alerts').append(
                    $('<div class="alert alert-success fade in">' +
                        '<a href="#" class="close" data-dismiss="alert">&times;</a>' +
                        'New item <strong>' +
                        data.items[0].name +
                        '</strong> was created successfuly.' +
                      '</div>')
                )
            }
        })
    })
    
    $('#project-add-item').click(function() {
        itemWiz[0].reset()
        $('#new-item').modal()
    })
    
    $('#new-item-published').change(function() {
        $('#new-item-publish-date').toggle()
    })
    
    $('#new-item-publish-date').datepicker({
        constrainInput: true,
        dateFormat: "dd-mm-yy"
    })
    
    /* New Template Wizard */
    
    var templateWiz = $('#new-template-wizard').wizard({
        btnNext: 'new-template-next',
        btnPrev: 'new-template-back'
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
        
        $.ajax('/api/templates', {
            method: 'POST',
            dataType: "json",
            data: JSON.stringify({
                project_id: projectId,
                name: $('#new-template-name').val(),
                type: $('#new-template-type').val(),
                do_import: $('#new-template-import').is(':checked'),
                import_from: $('#new-template-import-file').val(),
                data: $('#new-template-data').val()
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
    })
    
    $('#project-add-tmpl').click(function() {
        templateWiz[0].reset()
        $('#new-template').modal()
    })
    
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
    })
    
    $('#new-template-import').on('change', function() {
        // toggle disabled attribute on inputs
        $('#new-template-import-file').prop('disabled', function(i, v) { return !v; });
        $('#new-template-data').prop('disabled', function(i, v) { return !v; });
    })
    
    
    /* Page Wizard */
    var pageWiz = $('#new-page-wizard').wizard({
        btnNext: 'new-page-next',
        btnPrev: 'new-page-back'
    }).on('switched', function(ev) {
        if (ev.target.atTheEnd()) {
            // is it step to render template preview
            var template_id = $('#new-page-template').val()
            if (template_id) {
                $('#new-page-show-preview').attr('disabled', false)
            }
            else {
                $('#new-page-show-preview').attr('disabled', true)
            }
        }
    }).on('finished', function(ev) {
        $.ajax('/api/pages', {
            method: 'POST',
            dataType: "json",
            data: JSON.stringify({
                project_id: projectId,
                template_id: $("#new-page-template").val(),
                path: $('#new-page-path').val(),
                params: {}
            }),
            error: function(xhr, type, ex) {
                $().showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                $("#new-page").modal('hide')
                
                $('#dashboard-alerts').empty()
                $('#dashboard-alerts').append(
                    $('<div class="alert alert-success fade in">' +
                        '<a href="#" class="close" data-dismiss="alert">&times;</a>' +
                        'New page <strong>' +
                        data.pages[0].path +
                        '</strong> was created successfuly.' +
                      '</div>')
                )
                
                // update views
                pagesCnt.update()
                $().dataQuery('projects').filter({project_id: projectId}).one(renderProject)
            }
        })
    })
    
    $('#project-add-page').click(function() {
        pageWiz[0].reset()
        $('#new-page').modal()
    })
})