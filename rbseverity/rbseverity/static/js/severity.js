RBSeverity = {};


/*
 * Extends the comment dialog to provide buttons for severity.
 *
 * The Save button will be removed, and in its place will be a set of
 * buttons for choosing the severity level for the comment. The buttons
 * each work as save buttons.
 */
RBSeverity.CommentDialogHookView = Backbone.View.extend({
    events: {
        'click .buttons .save-severity': '_onSaveSeverityClicked'
    },

    buttonsTemplate: _.template([
        '<label for="SeverityListId">Severity:</label> ',
        '<select id="SeverityListId" class="severityClass">',
        ' <option class="comment-severity comment-severity-enhancement" value="enhancement">Enhancement</option>',
        ' <option class="comment-severity comment-severity-minor" value="minor">Minor</option>',
        ' <option class="comment-severity comment-severity-major" value="major">Major</option>',
        ' <option class="comment-severity comment-severity-critical" value="critical">Critical</option>',
        '</select>',
        '<br>',
        '    <label for="CategoryListId">Category:</label> ',
        '<select id="CategoryListId" class="categoryClass">',
        ' <option value="std">Standards</option>',
        ' <option value="func">Functional</option>',
        ' <option value="poor">Poor Practice</option>',
        ' <option value="logical">Logical</option>',
        ' <option value="ppt">Presetation/Documantation</option>',
        ' <option value="query">Query/Clarification/Recommendation</option>',
        '</select>',
        '<br>',
        '<span class="severity-actions">',
        '  <input type="button" class="save-severity" value="Save" ',
        '         disabled="true" />',
        '</span>'
    ].join('')),

    /*
     * Initializes the view.
     */
    initialize: function(options) {
        this.commentDialog = options.commentDialog;
        this.commentEditor = options.commentEditor;
    },

    /*
     * Renders the additions to the comment dialog.
     *
     * This will remove the Save button and set up the new buttons.
     */
    render: function() {
        var $severityButtons = $(this.buttonsTemplate());

        // Also making the 'Open an issue' option invisible. With the option to
        // mark the severity as 'Enhancement', this option does not make sense.
        this.commentDialog._$issueOptions.css({'visibility':'hidden'});
        this.commentDialog.$saveButton.remove();
        this.commentDialog.$buttons.prepend($severityButtons);

        $severityButtons.find('input')
            .bindVisibility(this.commentEditor, 'canEdit')
            .bindProperty('disabled', this.commentEditor, 'canSave', {
                elementToModel: false,
                inverse: true
            });

        /* Set a default severity, in case the user hits Control-Enter. */
/*        this.commentEditor.setExtraData('severity', 'enhancement'); */
    },

    /*
     * New function for saving data along with the severity.
     *
     * This will set the severity for the comment and then save it.
     */
    _onSaveSeverityClicked: function() {
        var severity = $(".severityClass").val();
        var category = $(".categoryClass").val();
        console.log(severity);
        if (this.commentEditor.get('canSave')) {
            this.commentEditor.setExtraData('severity', severity);
            this.commentEditor.setExtraData('category', category);
            this.commentDialog.save();
        }
    }
});


/*
 * Extends the review dialog to allow setting severities on unpublished
 * comments.
 *
 * A field will be provided that contains a list of severities to choose
 * from.
 *
 * If the comment does not have any severity set yet (meaning it's a pending
 * comment from before the extension was activated), a blank entry will be
 * added. If the severity is then set, the blank entry will go away the next
 * time it's loaded.
 */
RBSeverity.ReviewDialogCommentHookView = Backbone.View.extend({
    events: {
        'change select.severityClass': '_onSeverityChanged',
        'change select.categoryClass': '_onCategoryChanged'
    },

    template: _.template([
        '<label for="<%- id1 %>">Severity:</label> ',
        '<select id="<%- id1 %>" class="severityClass">',
        ' <option value="critical">Critical</option>',
        ' <option value="major">Major</option>',
        ' <option value="minor">Minor</option>',
        ' <option value="enhancement">Enhancement</option>',
        '</select>',
        '    <label for="<%- id2 %>">Category:</label> ',
        '<select id="<%- id2 %>" class="categoryClass">',
        ' <option value="std">Standards</option>',
        ' <option value="func">Functional</option>',
        ' <option value="poor">Poor Practice</option>',
        ' <option value="logical">Logical</option>',
        ' <option value="ppt">Presetation/Documantation</option>',
        ' <option value="query">Query/Clarification/Recommendation</option>',
        '</select>'
    ].join('')),

    /*
     * Renders the editor for a comment's severity and category.
     */
    render: function() {
        var severity = this.model.get('extraData').severity;
        var category = this.model.get('extraData').category;

        this.$el.html(this.template({
            id1: 'severity_' + this.model.id,
            id2: 'category_' + this.model.id
        }));

        this._$select1 = this.$("select#severity_"+this.model.id);
        // Also making the 'Open an issue' option invisible. With the option to
        // mark the severity as 'Enhancement', this option does not make sense.
	$('.issue-opened').css({visibility:'hidden'});
	$('.issue-opened').next().css({visibility:'hidden'});
        if (severity) {
            this._$select1.val(severity);
        } else {
            this._$select1.prepend($('<option selected/>'));
        }

        this._$select2 = this.$("select#category_"+this.model.id);

        if (category) {
            this._$select2.val(category);
        } else {
            this._$select2.prepend($('<option selected/>'));
        }

        return this;
    },

    /*
     * Handler for when the severity is changed by the user.
     *
     * Updates the severity on the comment to match.
     */
    _onSeverityChanged: function() {
        this.model.get('extraData').severity = this._$select1.val();
        console.log(this.model.get('extraData').severity);
    },

    /*
     * Handler for when the category is changed by the user.
     *
     * Updates the category on the comment to match.
     */
    _onCategoryChanged: function() {
        this.model.get('extraData').category = this._$select2.val();
        console.log(this.model.get('extraData').category);
    }
});



/*
 * Extends the review dialog to allow setting severities on unpublished
 * comments.
 *
 * A field will be provided that contains a list of severities to choose
 * from.
 *
 * If the comment does not have any severity set yet (meaning it's a pending
 * comment from before the extension was activated), a blank entry will be
 * added. If the severity is then set, the blank entry will go away the next
 * time it's loaded.
 */
RBSeverity.CommentIssueBarActionHookView = Backbone.View.extend({
    events: {
        'change select.causeClass': '_onCauseChanged',
        'change select.phaseClass': '_onPhaseChanged'
    },

    template: _.template([
        '<label for="<%- causeId %>">Defect Cause:</label> ',
        '<select id="<%- causeId %>" class="causeClass">',
        ' <option value="" selected>Select</option>',
        ' <option value="requirement">Ambigous Requirements</option>',
        ' <option value="design">Design Error</option>',
        ' <option value="stdfollow">Standards not followed</option>',
        ' <option value="stdupd">Standards needs updation</option>',
        ' <option value="knowledge">Lack of Knowledge</option>',
        ' <option value="oversight">Oversight</option>',
        ' <option value="dataerr">Data Error</option>',
        ' <option value="config">Incorrect Configuration</option>',
        ' <option value="hardware">Hardware Issue</option>',
        ' <option value="trace">Traceability Not followed</option>',
        '</select>',
        '    <label for="<%- phaseId %>">Phase Injected:</label> ',
        '<select id="<%- phaseId %>" class="phaseClass">',
        ' <option value="" selected>Select</option>',
        ' <option value="reqmt">Requirement</option>',
        ' <option value="design">Design</option>',
        ' <option value="code">Coding</option>',
        ' <option value="test">Testing</option>',
        '</select>'
    ].join('')),

    /*
     * Initializes the view.
     */
    initialize: function(options) {
        this.commentIssueBar = options.commentIssueBar;
        this.commentIssueManager = options.commentIssueManager;
    },


    /*
     * Renders the dropdowns for Defect cause and phase injected
     */
    render: function() {
        var $data = this.template({
            causeId: 'cause_' + this.commentIssueBar.options.commentID,
            phaseId: 'phase_' + this.commentIssueBar.options.commentID
        });

        this.$el.html($data);

        this._$causeSelect = this.$("select#cause_" + this.commentIssueBar.options.commentID);
        this._$phaseSelect = this.$("select#phase_" + this.commentIssueBar.options.commentID);

        console.log("Comment id:" + this.commentIssueBar.options.commentID);

        this.commentIssueManager.on('extraDataAvailable',
                                    this._onExtraDataAvailable,
                                    this);

        /* This function triggers the request for extraData for the comment.
           When it is available, _onExtraDataAvailable is called */
        this.commentIssueManager.getCommentExtraData(this.commentIssueBar.options.reviewID,
                                                     this.commentIssueBar.options.commentID,
                                                     this.commentIssueBar.options.commentType);

        return this;
    },

    /*
     * Handler for when extraData is available
     *
     * Updates the dispaly to reflect the data
     */
    _onExtraDataAvailable: function(comment) {

        if (comment.id === this.commentIssueBar.options.commentID) {
            this._extraData = comment.get('extraData');
            var cause = this._extraData.cause || null;
            var phase = this._extraData.phase || null;

            console.log("id: " + comment.id + " cause: " + cause + " phase:" + phase);
            /* Set the current value to the dropdowns */
            this._$causeSelect.val(cause);
            this._$phaseSelect.val(phase);
        }
    },

    /*
     * Handler for when Cause is changed by the user
     *
     * Saves the new value at the server
     */
    _onCauseChanged: function(comment) {
        console.log("new cause value:" + this._$causeSelect.val());
        console.log("old cause value:" + this._extraData.cause || null);
        this._extraData['cause'] = this._$causeSelect.val();
        
        this.commentIssueManager.setCommentExtraData(this.commentIssueBar.options.reviewID,
                                                     this.commentIssueBar.options.commentID,
                                                     this.commentIssueBar.options.commentType,
                                                     this._extraData);
    },

    /*
     * Handler for when Phase is changed by the user
     *
     * Saves the new value at the server
     */
    _onPhaseChanged: function(comment) {
        console.log("new phase value:" + this._$phaseSelect.val());
        console.log("old phase value:" + this._extraData.phase || null);
        this._extraData['phase'] = this._$phaseSelect.val();
        
        this.commentIssueManager.setCommentExtraData(this.commentIssueBar.options.reviewID,
                                                     this.commentIssueBar.options.commentID,
                                                     this.commentIssueBar.options.commentType,
                                                     this._extraData);
    }

});


/*
 * Extends Review Board with comment severity support.
 *
 * This plugs into the comment dialog and review dialog to add the ability
 * to set severities for comments.
 */
RBSeverity.Extension = RB.Extension.extend({
    initialize: function() {
        _super(this).initialize.call(this);

        new RB.CommentDialogHook({
            extension: this,
            viewType: RBSeverity.CommentDialogHookView
        });

        new RB.ReviewDialogCommentHook({
            extension: this,
            viewType: RBSeverity.ReviewDialogCommentHookView
        });

        new RB.CommentIssueBarActionHook({
            extension: this,
            viewType: RBSeverity.CommentIssueBarActionHookView
        });
    }
});
