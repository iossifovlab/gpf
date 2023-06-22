* score resource
    - should return None when a histogram file is not created.

* rename annotators
    - effect_annotator -> gpf_effect
    - liftover_annotator -> liftover

* updated the font sized in the pipeline documentation: 
    - larger fonts for the attribute names
    - smaller fonts for the annotators

* score annotator
    - re-organized the responsibilities for generatonr score documentation 
        - the ScoreResource itself should bult some of the documentatio and the annotator should add the annotator specific options, like the aggregators.
    - configure completely few of the score resources
        - create a brange in the ivan's local grr repo
        - copy the available docuemntation from dbSNP
    - re-implemenet the aggregator documentation by using the score resources implementation

* GRR index page
    - make sure that resources provide two properties:
        - summary 
        - description 
        (OR description and documentation)
    - make sure that only the resoruce "summary" is included ine index.

* gpf_effect annotator
    - implement the <effect>_genes attributes
    - implement the <effect>_transcripts attributes
    - add the appropriate annotator documentation

