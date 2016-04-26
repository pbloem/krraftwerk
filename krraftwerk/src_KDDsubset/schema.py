#!/usr/bin/env python3

import rdflib

def addSubClassOf(graph, nss, subclass, superclasses):
    for superclass in superclasses:
        graph.add((subclass, \
                  rdflib.URIRef(nss['rdfs'] + 'subClassOf'), \
                  superclass))

def addProp(graph, nss, prop, domains, range=None):
    for domain in domains:
        graph.add((prop, \
                  rdflib.URIRef(nss['rdfs'] + 'domain'), \
                  domain))

    if range is not None:
        graph.add((prop, \
                  rdflib.URIRef(nss['rdfs'] + 'range'), \
                  range))

def addSubPropOf(graph, nss, prop, superprops, domain=None, range=None):
    addProp(graph, nss, prop, domain, range)

    for superprop in superprops:
        graph.add((prop, \
                  rdflib.URIRef(nss['rdfs'] + 'subPropertyOf'), \
                  superprop))

def generate(graph, nss):
    # ID
    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_hasID'), \
                 [ rdflib.URIRef(nss['dcterms'] +'identifier') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Affiliation'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Author'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Conference'), \
                   rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Journal'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Paper'), \
                   rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'ID'))

    # affiliations
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_Affiliation'), \
                  [ rdflib.URIRef(nss['foaf'] + 'Organization'), \
                    rdflib.URIRef(nss['SWRC'] + 'Organization') ])

    # authors
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_Author'), \
                  [ rdflib.URIRef(nss['foaf'] + 'Person'), \
                    rdflib.URIRef(nss['SWRC'] + 'Person') ])

    # conferences
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_Conference'), \
                  [ rdflib.URIRef(nss['foaf'] + 'Organization'), \
                    rdflib.URIRef(nss['SWRC'] + 'Organization') ])

    # fields of study
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy'), \
                  [ rdflib.URIRef(nss['skos'] + 'Concept') ])

    # journals
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_Journal'), \
                  [ rdflib.URIRef(nss['SWRC'] + 'Journal') ])

    # papers
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_Paper'), \
                  [ rdflib.URIRef(nss['SWRC'] + 'Publication') ])

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_title'), \
                 [ rdflib.URIRef(nss['dcterms'] +'title') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'string'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_yearOfPublication'), \
                 [ rdflib.URIRef(nss['dcterms'] +'date') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'gYear'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_dateOfPublication'), \
                 [ rdflib.URIRef(nss['dcterms'] +'issued') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'Date'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_doi'), \
                 [ rdflib.URIRef(nss['bibo'] +'doi') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'ID'))

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_rank'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
            rdflib.URIRef(nss['xsd'] + 'positiveInteger'))

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_nrOfTimesCited'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
            rdflib.URIRef(nss['xsd'] + 'positiveInteger'))
    
    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_publishedIn'), \
                 [ rdflib.URIRef(nss['dcterms'] +'partOf') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Journal'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_published'), \
                 [ rdflib.URIRef(nss['dcterms'] +'hasPart') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Journal') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Paper'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_presentedAt'), \
                 [ rdflib.URIRef(nss['bibo'] + 'presentedAt'), \
                   rdflib.URIRef(nss['swc'] + 'relatedToEvent') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_presented'), \
                 [ rdflib.URIRef(nss['bibo'] + 'presents'), \
                   rdflib.URIRef(nss['swc'] + 'hasRelatedDocument') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Paper'))

    # conference instances
    addSubClassOf(graph, nss, \
                  rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance'), \
                  [ rdflib.URIRef(nss['SWRC'] + 'Conference'), \
                    rdflib.URIRef(nss['swc'] + 'ConferenceEvent'), \
                    rdflib.URIRef(nss['conf'] + 'Conference') ])

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_organized'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_Conference') ], \
            rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance'))

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_organizedBy'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
            rdflib.URIRef(nss['base'] + 'MAG_Conference'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_url'), \
                 [ rdflib.URIRef(nss['dcterms'] +'seeAlso') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'anyURI'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_location'), \
                 [ rdflib.URIRef(nss['swc'] +'hasLocation') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['geo'] + 'SpatialThing'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_yearOfOccurence'), \
                 [ rdflib.URIRef(nss['dcterms'] +'date') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'gYear'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_startDate'), \
                 [ rdflib.URIRef(nss['conf'] +'startdate') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'Date'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_endDate'), \
                 [ rdflib.URIRef(nss['conf'] +'endDate') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'Date'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_abstractDueOn'), \
                 [ rdflib.URIRef(nss['conf'] +'abstractDueOn') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'Date'))

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_submissionDueOn'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
            rdflib.URIRef(nss['xsd'] + 'Date'))

    addProp(graph, nss, \
            rdflib.URIRef(nss['base'] + 'MAG_notificationDueOn'), \
            [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
            rdflib.URIRef(nss['xsd'] + 'Date'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_finalDueOn'), \
                 [ rdflib.URIRef(nss['conf'] +'paperDueOn') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance') ], \
                 rdflib.URIRef(nss['xsd'] + 'Date'))

    # paper author affiliations
    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_author'), \
                 [ rdflib.URIRef(nss['dcterms'] +'creator'), \
                   rdflib.URIRef(nss['SWRC'] + 'creator'), \
                   rdflib.URIRef(nss['foaf'] + 'maker') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Author'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_authorOf'), \
                 [ rdflib.URIRef(nss['foaf'] + 'made') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Author') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Paper'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_affiliatedWith'), \
                 [ rdflib.URIRef(nss['SWRC'] + 'affiliation') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Author') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Affiliation'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_hasMember'), \
                 [ rdflib.URIRef(nss['foaf'] + 'member') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Affiliation') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Author'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_firstAuthor'), \
                 [ rdflib.URIRef(nss['base'] +'author') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Author'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_secondAuthor'), \
                 [ rdflib.URIRef(nss['base'] +'author') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Author'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_thirdAuthor'), \
                 [ rdflib.URIRef(nss['base'] +'author') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Author'))

    # paper keyword
    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_keyword'), \
                 [ rdflib.URIRef(nss['foaf'] + 'topic') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['xsd'] + 'string'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_keyword'), \
                 [ rdflib.URIRef(nss['foaf'] + 'topic') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper'), \
                   rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy') ], \
                 rdflib.URIRef(nss['xsd'] + 'string'))

    # paper reference
    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_cites'), \
                 [ rdflib.URIRef(nss['bibo'] + 'cites') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Paper'))

    addSubPropOf(graph, nss, \
                 rdflib.URIRef(nss['base'] + 'MAG_citedBy'), \
                 [ rdflib.URIRef(nss['bibo'] + 'isReferencedBy') ], \
                 [ rdflib.URIRef(nss['base'] + 'MAG_Paper') ], \
                 rdflib.URIRef(nss['base'] + 'MAG_Paper'))
