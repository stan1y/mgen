/* MGEN: Static Website Generator
 * Dashboard UI magic
 */

var projects = $().dataQuery('projects')

var refreshDashboard = function() {
    $("#dashboard-overview").empty()
    $("#dashboard-progress").show();
    projects.fetch(function(data) {
        $("#dashboard-progress").hide();
    })
}

$(document).ready(function() {
    
    refreshDashboard()
    
    $(projects).on('loaded', function(ev, query) {
        // populate dashboard overview
        // and projects selector
        var overview = $('#dashboard-overview')
        var projectSelector = $("#projects-selector")
        var currentRow = $('<div class="dashboard row"></div>')
        var projectIdx = 0
        
        overview.empty()
        overview.append(currentRow)
        query.data.forEach( function(proj) {
            
            if (projectIdx % 3 == 0) {
                currentRow = $('<div class="dashboard row"></div>')
                overview.append(currentRow)
            }
            
            currentRow.append(
                $('<div class="dashboard col-xs-6 col-md-4">' +
                    '<a href="/project/' + proj.id + '">' +
                    '<h2>' + proj.title + '</h2></a>' +
                    '<h4>' + proj.public_base_uri + '</h4>' +
                    '<ul> ' +
                        '<li>4 Page Templates</li>' +
                        '<li>19 Pages</li>' +
                        '<li>31 Items in 2 Sequences</li>' +
                    '</ul>' +
                '</div>')
            )
            
            projectSelector.append(
                $('<li>' +
                    '<a href="/api/project/' + proj.id + '">' +
                        proj.title +
                    '</a>' +
                '</li>')
            )
            
            projectIdx++;
        })
        
        // add separator and new project selection
        if (query.data.length > 0)
            projectSelector.append($('<li role="separator" class="divider"></li>'))
        
        projectSelector.append($('<li>' +
            '<a data-toggle="modal" data-target="#new-project">New Project</a>' + 
            '</li>'))
    })
    
    
    $('#new-project-create').click(function() {
        $.ajax('/projects', {
            method: "POST",
            dataType: "json",
            data: {
                title: $('#new-project-title').val(),
                public_base_uri: $('#new-project-uri').val(),
                options: {
                    enable_robots: $('#new-project-enable-robots').attr('checked'),
                    enable_sitemap: $('#new-project-enable-sitemap').attr('checked')
                }
            },
            error: function(xhr, type, ex) {
                $.showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                $("#new-project").modal("hide")
                $('#dashboard-alerts').empty()
                $('#dashboard-alerts').append(
                    $('<div class="alert alert-success fade in">' +
                        '<a href="#" class="close" data-dismiss="alert">&times;</a>' +
                        '<strong>Hurray!</strong> Your new project ' +
                        data.projects[0].title +
                        ' was created successfuly.' +
                      '</div>')
                )
                refreshDashboard()
            }
        })
    })
})

