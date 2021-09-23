import { IdName } from "app/common/idname";
import { Column, ColumnGroup, PersonFilter, PersonSetCollection, PersonSetCollections } from "./datasets";
import { PersonSet } from "./datasets";

describe('PersonSet', () => {

    it('should create person set from json', () => {
        const mockPerson1 = PersonSet.fromJson({
            id: 'id1',
            name: 'name1',
            values: ['value1', 'value2'],
            color: 'color1'
        });

        expect(new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1')).toEqual(mockPerson1);
    });

    it('should create person from array of json', () => {

        const mockPerson2 = PersonSet.fromJsonArray([
            {
                id: 'id1',
                name: 'name1',
                values: ['value1', 'value2'],
                color: 'color1'
            },
            {
                id: 'id2',
                name: 'name2',
                values: ['value2', 'value3'],
                color: 'color2'
            }
        ]);
        expect([
            new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1'),
            new PersonSet('id2', 'name2', ['value2', 'value3'], 'color2')
        ]).toEqual(mockPerson2);
    });

});

describe('PersonSetCollection', () => {
    it('should create person set collection from json array', () => {
        const mockPersonSetCollection1 = [
            new PersonSetCollection('id1', 'name1', 'id1',
            new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1'),
            [
                new PersonSet('id1', 'name2', ['value2', 'value2'], 'color3'),
                new PersonSet('id2', 'name3', ['value2', 'value3'], 'color4')
            ]),
            new PersonSetCollection('id2', 'name2', 'id2',
            new PersonSet('id2', 'name2', ['value3', 'value4'], 'color2'),
            [
                new PersonSet('id2', 'name3', ['value3', 'value3'], 'color5'),
                new PersonSet('id3', 'name4', ['value3', 'value4'], 'color6')
            ])
        ];

        const mockPersonSetCollection2 = PersonSetCollection.fromJson({
            id1: {
                id: 'id1',
                name: 'name1',
                source: 'source1',
                default: {
                    id: 'id1',
                    name: 'name1',
                    values: ['value1', 'value2'],
                    color: 'color1'
                },
                domain: [
                    {
                        id: 'id1',
                        name: 'name2',
                        values: ['value2', 'value2'],
                        color: 'color3'
                    },
                    {
                        id: 'id2',
                        name: 'name3',
                        values: ['value2', 'value3'],
                        color: 'color4'
                    }
                ]
            },
            id2: {
                id: 'id2',
                name: 'name2',
                source: 'source2',
                default: {
                    id: 'id2',
                    name: 'name2',
                    values: ['value3', 'value4'],
                    color: 'color2'
                },
                domain: [
                    {
                        id: 'id2',
                        name: 'name3',
                        values: ['value3', 'value3'],
                        color: 'color5'
                    },
                    {
                        id: 'id3',
                        name: 'name4',
                        values: ['value3', 'value4'],
                        color: 'color6'
                    }
                ]
            }
        });
        expect(mockPersonSetCollection1).toEqual(mockPersonSetCollection2);

    });
});

describe('PersonSetCollections', () => {
    it('should create person set collections from json', () => {
        const mockPersonSetCollections1 = new PersonSetCollections([
            new PersonSetCollection('id1', 'name1', 'id1',
            new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1'),
            [
                new PersonSet('id1', 'name2', ['value2', 'value2'], 'color3'),
                new PersonSet('id2', 'name3', ['value2', 'value3'], 'color4')
            ]),
            new PersonSetCollection('id2', 'name2', 'id2',
            new PersonSet('id2', 'name2', ['value3', 'value4'], 'color2'),
            [
                new PersonSet('id2', 'name3', ['value3', 'value3'], 'color5'),
                new PersonSet('id3', 'name4', ['value3', 'value4'], 'color6')
            ])
        ]);

        const mockPersonSetCollections2 = PersonSetCollections.fromJson({
            id1: {
                name: 'name1',
                default: {
                    id: 'id1',
                    name: 'name1',
                    values: ['value1', 'value2'],
                    color: 'color1'
                },
                domain: [
                    {
                        id: 'id1',
                        name: 'name2',
                        values: ['value2', 'value2'],
                        color: 'color3'
                    },
                    {
                        id: 'id2',
                        name: 'name3',
                        values: ['value2', 'value3'],
                        color: 'color4'
                    }
                ]
            },
            id2: {
                name: 'name2',
                default: {
                    id: 'id2',
                    name: 'name2',
                    values: ['value3', 'value4'],
                    color: 'color2'
                },
                domain: [
                    {
                        id: 'id2',
                        name: 'name3',
                        values: ['value3', 'value3'],
                        color: 'color5'
                    },
                    {
                        id: 'id3',
                        name: 'name4',
                        values: ['value3', 'value4'],
                        color: 'color6'
                    }
                ]
            }
        });

        expect(mockPersonSetCollections1).toEqual(mockPersonSetCollections2);
    });

    it('should get legend from person set collection', () => {
        const mockPersonSetCollections1 = new PersonSetCollections([
            new PersonSetCollection('id1', 'name1', 'id1',
            new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1'),
            [
                new PersonSet('id1', 'name2', ['value2', 'value2'], 'color3'),
                new PersonSet('id2', 'name3', ['value2', 'value3'], 'color4')
            ]),
            new PersonSetCollection('id2', 'name2', 'id2',
            new PersonSet('id2', 'name2', ['value3', 'value4'], 'color2'),
            [
                new PersonSet('id2', 'name3', ['value3', 'value3'], 'color5'),
                new PersonSet('id3', 'name4', ['value3', 'value4'], 'color6')
            ])
        ]);

        const mockPersonSetCollections2 = [];
        mockPersonSetCollections2.push(new PersonSet('id1', 'name2', ['value2', 'value2'], 'color3'));
        mockPersonSetCollections2.push(new PersonSet('id2', 'name3', ['value2', 'value3'], 'color4'));
        mockPersonSetCollections2.push({'color': '#E0E0E0', 'id': 'missing-person', 'name': 'missing-person'});

        expect(mockPersonSetCollections1.getLegend(mockPersonSetCollections1.collections[0]))
            .toEqual(mockPersonSetCollections2);
    });
});

describe('PersonFilter', () => {
    it('should create person filter instance from json', () => {

        const mockPersonFilter1 = PersonFilter.fromJson({
            name: {
                name: 'name1',
                from: 'from1',
                source: 'source1',
                source_type: 'sourceType1',
                filter_type: 'filterType1',
                role: 'role1',
            },
            name1: {
                name: 'name2',
                from: 'from2',
                source: 'source2',
                source_type: 'sourceType2',
                filter_type: 'filterType2',
                role: 'role2',
            }
        });

        const mockPersonFilter2 = [
            new PersonFilter('name1', 'from1', 'source1', 'sourceType1', 'filterType1', 'role1'),
            new PersonFilter('name2', 'from2', 'source2', 'sourceType2', 'filterType2', 'role2')
        ];

        expect(mockPersonFilter1).toEqual(mockPersonFilter2);
    });
});

describe('Column', () => {
    it('should create column from json', () => {
        expect(new Column('name', 'source',  'format')).toEqual(Column.fromJson({
            name: 'name',
            source: 'source',
            format: 'format'
        }));
    });
});

describe('ColumnGroup', () => {
    it('should create column group from json', () => {
        const columnGroupMock1 = new ColumnGroup('name1', [
            new Column('name1', 'source1',  'format1'),
            new Column('name2', 'source2',  'format2')
        ]);

        const columnGroupMock2 = ColumnGroup.fromJson({
            name: 'name1',
            columns: [
                {
                    name: 'name1',
                    source: 'source1',
                    format: 'format1'
                },
                {
                    name: 'name2',
                    source: 'source2',
                    format: 'format2'
                }
            ]
        });

        expect(columnGroupMock1).toEqual(columnGroupMock2);
    });
});
