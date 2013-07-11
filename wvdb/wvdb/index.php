<!DOCTYPE html>
<html>
    <head>
        <title>Variants DataBase</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <link href="bootstrap/css/bootstrap.css" rel="stylesheet">        
        <link href="slider/css/slider.css" rel="stylesheet">        
    </head>
    <body>
        <div class="container">
            <h1>Variants Database</h1>
            <p>Experimental interface to the getVariants.py command line tool.</p>

            <form class="well">  
                <div class="well">
                <label><h4>Denovo Studies</h4></label>                  
                <div class="control-group">  
                    <label class="control-label" for="select01" >You select none, one or multiple. (hold the Ctrl key down to select more than one study.)</label>  
                    <div class="controls">  
                        <select id="select01" multiple="multiple"size="10">  
                            <option>all</option>  
                            <option>allPublishedPlusOurRecent</option>  
                            <option>allPublished</option>  
                            <option>wig683</option>  
                            <option>IossifovWE2012</option>  
                            <option>DalyWE2012</option>  
                            <option>StateWE2012</option>  
                            <option>EichlerWE2012</option>  
                            <option>allPublishedWEWithOurCallsAndTG</option>                  
                        </select>  
                    </div>  
                </div>  
                
                <label class="checkbox">  
                    <input type="checkbox">Click this to search denovo variants only. (The transmitted studies you picked will be ignored.)
                </label>  
                </div>
        
                <div class="well">
                <label><h4>Transmitted Studies</h4></label>                  
                <div class="control-group">  
                    <label class="control-label" for="select02" >You select none, one or multiple. (hold the Ctrl key down to select more than one study.)</label>  
                    <div class="controls">  
                        <select id="select02" multiple="multiple"size="10">  
                            <option>all</option>  
                            <option>allPublishedPlusOurRecent</option>  
                            <option>allPublished</option>  
                            <option>wig683</option>  
                            <option>IossifovWE2012</option>  
                            <option>DalyWE2012</option>  
                            <option>StateWE2012</option>  
                            <option>EichlerWE2012</option>  
                            <option>allPublishedWEWithOurCallsAndTG</option>                  
                        </select>  
                    </div>  
                </div>  
                
                <label class="checkbox">  
                    <input type="checkbox">Click this to search transmitted variants only. (The denovo studies you picked will be ignored.)
                </label>  
                </div>
                <div class="well">
                <label><h4>Effect Type</h4></label>                  
                <div class="control-group">  
                    <label class="control-label" for="select03" >You select none, one or multiple. (hold the Ctrl key down to select more than one study.)</label>  
                    <div class="controls">  
                        <select id="select03" multiple="multiple"size="6">                              
                            <option>frame-shift</option>  
                            <option>nonsense</option>  
                            <option>splice-site</option>  
                            <option>no-frame-shift-new-stop</option>  
                            <option>missense</option>  
                            <option>non-frame-shift</option>  
                        </select>  
                    </div>  
                </div>  
                </div>
                
                <div class="well">
                <label><h4>Variant Types</h4></label>                  
                <div class="control-group">  
                    <label class="control-label" for="select04" >You select none, one or multiple. (hold the Ctrl key down to select more than one study.)</label>  
                    <div class="controls">  
                        <select id="select04" multiple="multiple"size="3">                              
                            <option>sub</option>  
                            <option>ins</option>  
                            <option>del</option>  
                        </select>  
                    </div>  
                </div>  
                </div>     
                
                <div class="well">
                 <label>Pop Frequency Max</label>  
                 <input type="text" value="100" data-slider-min="-1" data-slider-max="100" data-slider-step="1" id="popFrequencyMax" >
                 <span class="help-inline"> maximum population frequency in percents. Can be 100 or -1 for no limit; ultraRare. 1.0 by default. </span>  
               </div>
                
                <div class="well">
                 <label>Pop Frequency Min</label>  
                 <input type="text" value="-1" data-slider-min="-1" data-slider-max="100" data-slider-step="1" id="popFrequencyMin" >
                 <span class="help-inline"> minimum population frequency in percents. Can be -1 for no limit. -1 by default. </span>  
               </div>                

                
                <div class="well">
                <label><h4>In Child</h4></label>                  
                <div class="control-group">  
                    <label class="control-label" for="select05" >You select none, one or multiple. (hold the Ctrl key down to select more than one study.)</label>  
                    <div class="controls">  
                        <select id="select05" multiple="multiple"size="6">                              
                            <option value="prb">Proband</option>  
                            <option value="sib">Sibling</option>  
                            <option value="prbM">Proband Male</option>  
                            <option value="prbF">Proband Female</option>  
                            <option value="sibM">Sibling Male</option>  
                            <option value="sibF">Sibling Female</option>                              
                        </select>  
                    </div>  
                </div>  
                </div> 
                
                
                <div class="well">
                <label><h4>Families</h4></label>                  
            –familiesFile 	a file with a list of the families to report 	
            –familiesList 	comma separated llist of the familyIds 	
                </div> 
                
                <div class="well">
                <label><h4>Gene Sets</h4></label>                  
            –geneSet 	gene set id of the form “collection:setid 	
            –geneSym 		
            –geneSymFile 	the first column should cotain gene symbols 	
            –geneId 	list of gene ids 	
            –geneIdFile 	the first column should cotain gene ids 	
                </div> 
                
                <div class="well">
                <label><h4>Region</h4></label>   
                –regionS 	region             
                </div> 
                
                <button type="submit" class="btn">Get Variants</button>  
            </form>  
            
            


        </div>        
        <script src="jquery-1.10.1.min.js"></script>            
        <script src="bootstrap/js/bootstrap.js"></script>     
        <script src="slider/js/bootstrap-slider.js"></script>     
        <script src="index.js"></script>     
    </body>
</html>


