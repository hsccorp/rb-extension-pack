PDFReviewable = RB.FileAttachmentReviewable.extend({
	  defaults: _.defaults({
        //imageURL: ''
        //diffAgainstImageURL: ''
    }, RB.FileAttachmentReviewable.prototype.defaults),

    commentBlockModel: RB.RegionCommentBlock
});
