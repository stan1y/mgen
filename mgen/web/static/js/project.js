/* MGEN: Static Website Generator
 * Dashboard UI magic
 */

var projects = new MGEN.DataStore("projects")
var items = new MGEN.DataStore("items")

var renderProject = function(proj) {
    console.log(proj)
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
        })
    })
    
    $('#new-item-published').change(function() {
        $('#new-item-publish-date').toggle()
    })
    
    $('#new-item-publish-date').datepicker({
        constrainInput: true,
        dateFormat: "dd-mm-yy"
    });
})