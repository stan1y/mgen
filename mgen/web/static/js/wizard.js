/*
 * MGEN Wizard jQuery plugin
 */
 
(function ( $ ) {
    
    var animationEnd = 'webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend'
    
    var Wizard = function(el, options) {
        this.options = $.extend({
            animate: true,
            animateShow: "fadeIn",
            animateHide: "fadeOut",
            btnNext: "wizard-next",
            btnPrev: "wizard-prev",
            btnNextText: "Next",
            btnFinishText: "Finish",
            btnBackText: "Back",
            btnCancelText: "Cancel"
        }, options)
        
        this.el = $(el)
        this.steps = this.el.find('div.step')
        this.currentStep = $(this.el.find('div.step.first')[0])
        this.currentStepIdx = 0
        this.btnNext = $('#' + this.options.btnNext)
        this.btnPrev = $('#' + this.options.btnPrev)
        
        var self = this;
        this.btnNext.click(function() {
            self.forward()
        })
        this.btnPrev.click(function() {
            self.back()
        })
        
        this.steps.hide()
        this.currentStep.show()
        return this
    }
    
    Wizard.prototype.reset = function() {
        this.el.parent('form')[0].reset()
        this.steps.hide()
        this.currentStepIdx = 0
        this.currentStep = $(this.el.find('div.step.first')[0])
        this.currentStep.show()
        this._updateBtns()
        return this
    }
    
    Wizard.prototype._updateBtns = function() {
        
        if (this.currentStepIdx >= this.steps.length - 1) {
            // reached end
            this.btnNext.text(this.options.btnFinishText)
            this.btnPrev.text(this.options.btnBackText)
        }
        else {
            this.btnNext.text(this.options.btnNextText)
            if (this.currentStepIdx == 0) {
                this.btnPrev.text(this.options.btnCancelText)
            }
        }
    }
    
    Wizard.prototype.switch = function(idx) {
        var nextStep = this.steps[idx],
            toshow = $(nextStep),
            tohide = $(this.currentStep)

        if (this.options.animate) {
            tohide.show()
            toshow.show()
            
            toshow.css({position: 'absolute'})
            tohide.css({position: 'relative'})
            tohide.css({float: 'left'})
            
            toshow.one(animationEnd, function() {
                tohide.hide()
                toshow.css({position: ''})
                tohide.css({position: ''})
                tohide.css({float: ''})
            })
            
            tohide.animateCss(this.options.animateHide)
            toshow.animateCss(this.options.animateShow)
        }
        else {
            tohide.hide()
            toshow.show()
        }
        this.currentStep = $(nextStep)
        this._updateBtns()
        $(this).trigger('switched')
    }
    
    Wizard.prototype.atTheEnd = function() {
        return (this.currentStepIdx >= this.steps.length - 1)
    }
    
    Wizard.prototype.atTheBegining = function() {
        return (this.currentStep == 0)
    }
    
    Wizard.prototype.forward = function() {
        if (this.atTheEnd()) {
            // at the last step, close dialog
            this.el.parents('.modal').modal('hide')
            $(this).trigger('finished')
            return
        }
        this.currentStepIdx += 1
        this.switch(this.currentStepIdx)
    }
    
    Wizard.prototype.back = function() {
        if (this.atTheBegining()) {
            // at the first step, close dialog
            this.el.parents('.modal').modal('hide')
            $(this).trigged('canceled')
            return
        }
        this.currentStepIdx -= 1
        this.switch(this.currentStepIdx)
    }
 
    $.fn.wizard = function(options) {
        return $(new Wizard(this, options))
    }
    
    $.fn.animateCss = function (animationName) {
        this.addClass('animated ' + animationName).one(animationEnd, function() {
            $(this).removeClass('animated ' + animationName)
        })
    }
 
}( jQuery ));