/* MGEN: Static Website Generator
 * Dashboard UI magic
 */

var projects = new MGEN.DataStore("projects")
var items = new MGEN.DataStore("items")

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

var refreshProjectItems = function(projectId) {
    var itemsCnt = $('#project-items')
    var currentRow = $('<div class="row"></div>')
    var itemIdx = 0
    
    itemsCnt.empty()
    itemsCnt.append(currentRow)
    $("#progress-items").show()
    
    items.query().filter({project_id: projectId}).fetch(function(fetched) {
        $("#progress-items").hide()
        fetched.forEach(function(item) {
            if (itemIdx % 3 == 0) {
                currentRow = $('<div class="row"></div>')
                itemsCnt.append(currentRow)
            }
            
            currentRow.append(
                $('<div class="col-xs-6 col-md-4">' +
                    '<h2>' + item.name + '</h2>' +
                    '<h4>' + item.type + '</h4>' +
                    '<pre>'+ item.body.substring(0, 50) + '</pre>' +
                '</div>')
            )
            
            itemIdx++
        })
        
        if (fetched.length == 0) {
            itemsCnt.append($('<p>' +
                              'There are no items in this project.' +
                              '<a id="project-items-refresh">retry?</a>' +
                              '</p>'))
        }
    })
}

var refreshProjectTemplates = function(projectId) {
    
}

$(document).ready(function() {
    var projectId = $('#project-id').val()
    projects.get(projectId, renderProject)
    
    $('#new-item-create').click(function() {
        var tags = $('#new-item-tags').val();
        items.add({
            'project_id': projectId,
            'name': $('#new-item-name').val(),
            'uri_path': $('#new-item-uri').val(),
            'type': $('#new-item-type').val(),
            'tags': tags.length > 0 ? tags.split(',') : [],
            'published': $('#new-item-published').attr('checked') == 'checked',
            'publish_on': $('#new-item-publish-date').val(),
            'body': $('#new-item-body').val()
        }, function(item) {
            ("#new-item-create").modal('hide')
            $('#dashboard-alerts').empty()
            $('#dashboard-alerts').append(
                $('<div class="alert alert-success fade in">' +
                    '<a href="#" class="close" data-dismiss="alert">&times;</a>' +
                    'New item <strong>' +
                    item.name +
                    '</strong> was created successfuly.' +
                  '</div>')
            )
            refreshProjectItems(projectId);
        })
    })
    
    $('#new-item-published').change(function() {
        $('#new-item-publish-date').toggle()
    })
    
    $('#new-item-publish-date').datepicker({
        constrainInput: true,
        dateFormat: "dd-mm-yy"
    })
    
    $('#new-item-wizard').wizard({
        btnNext: 'new-item-next',
        btnPrev: 'new-item-back'
    })
    
    // refresh project details on page load
    refreshProjectItems(projectId)
    refreshProjectTemplates(projectId)
})